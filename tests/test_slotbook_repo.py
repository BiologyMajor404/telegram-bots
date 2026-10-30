"""SlotBook booking status changes run against a real (SQLite) database: each one is a
conditional UPDATE, so a payment, the expiry job and button presses can't both win.
Postgres runs the same statements; SQLite stands in so the tests need no server.
Separate sessions play the concurrent actors, each holding its own view of the booking."""

import asyncio
from datetime import UTC, datetime, timedelta

import pytest

pytest.importorskip("aiosqlite")

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from slotbook import repo
from slotbook.models import Base, Booking, BookingStatus, Service

NOW = datetime(2026, 11, 2, 12, tzinfo=UTC)


@pytest.fixture
def run(tmp_path):
    """run(scenario) calls `await scenario(sessions)` on a fresh DB with one service."""

    def runner(scenario):
        async def main():
            engine = create_async_engine(f"sqlite+aiosqlite:///{(tmp_path / 'db').as_posix()}")
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            sessions = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
            try:
                async with sessions() as session:
                    session.add(Service(id=1, name="Cut", duration_min=60, price=100))
                    await session.commit()
                return await scenario(sessions)
            finally:
                await engine.dispose()

        return asyncio.run(main())

    return runner


async def add(sessions, **fields) -> int:
    values = {
        "user_id": 5,
        "user_name": "Ann",
        "service_id": 1,
        "starts_at": NOW + timedelta(days=2),
        "ends_at": NOW + timedelta(days=2, hours=1),
        "status": BookingStatus.PENDING,
        "deposit_stars": 50,
        "created_at": NOW,
    } | fields
    async with sessions() as session:
        booking = Booking(**values)
        session.add(booking)
        await session.commit()
        return booking.id


async def load(sessions, booking_id) -> tuple[AsyncSession, Booking]:
    session = sessions()
    return session, await session.get(Booking, booking_id)


def test_payment_confirms_a_hold_once(run):
    async def scenario(sessions):
        booking_id = await add(sessions)
        (s1, first), (s2, second) = (
            await load(sessions, booking_id),
            await load(sessions, booking_id),
        )
        # Two copies of the invoice paid at once: both saw the hold waiting for payment
        results = (
            await repo.activate_paid(s1, first, "A"),
            await repo.activate_paid(s2, second, "B"),
        )
        await s1.close()
        await s2.close()
        return results, second.status, second.payment_charge_id

    assert run(scenario) == ((True, False), BookingStatus.ACTIVE, "A")


def test_expiry_and_payment_at_once_dont_both_win(run):
    async def scenario(sessions):
        booking_id = await add(sessions, created_at=NOW - timedelta(minutes=20))
        session, booking = await load(sessions, booking_id)
        async with sessions() as job:
            expired = await repo.expire_unpaid(job, NOW - timedelta(minutes=15))
        paid = await repo.activate_paid(session, booking, "A")
        await session.close()
        return len(expired), paid, booking.status

    # Expiry came first, so the payment must not revive the hold (it's refunded instead)
    assert run(scenario) == (1, False, BookingStatus.EXPIRED)


def test_expiry_releases_only_old_unpaid_holds(run):
    async def scenario(sessions):
        old = await add(sessions, created_at=NOW - timedelta(minutes=20))
        await add(sessions, created_at=NOW - timedelta(minutes=5))
        await add(sessions, status=BookingStatus.ACTIVE, created_at=NOW - timedelta(minutes=20))
        async with sessions() as session:
            expired = await repo.expire_unpaid(session, NOW - timedelta(minutes=15))
            statuses = list(await session.scalars(select(Booking.status).order_by(Booking.id)))
        return [(b.id, b.status) for b in expired] == [(old, BookingStatus.EXPIRED)], statuses

    assert run(scenario) == (
        True,
        [BookingStatus.EXPIRED, BookingStatus.PENDING, BookingStatus.ACTIVE],
    )


def test_late_payment_is_recorded_once_and_owed_back(run):
    async def scenario(sessions):
        booking_id = await add(sessions, status=BookingStatus.EXPIRED)
        async with sessions() as session:
            booking = await session.get(Booking, booking_id)
            first = await repo.record_late_payment(session, booking, "A")
            again = await repo.record_late_payment(session, booking, "A")  # update came twice
            return first, again, booking.payment_charge_id, booking.refund_owed

    assert run(scenario) == (True, False, "A", True)


def test_extra_payment_doesnt_overwrite_the_stored_one(run):
    async def scenario(sessions):
        booking_id = await add(sessions, status=BookingStatus.ACTIVE, payment_charge_id="A")
        async with sessions() as session:
            booking = await session.get(Booking, booking_id)
            recorded = await repo.record_late_payment(session, booking, "B")
            return recorded, booking.payment_charge_id, booking.refund_owed

    assert run(scenario) == (False, "A", False)


def test_double_tap_on_cancel_cancels_once(run):
    async def scenario(sessions):
        booking_id = await add(sessions, status=BookingStatus.ACTIVE, payment_charge_id="A")
        (s1, tap1), (s2, tap2) = await load(sessions, booking_id), await load(sessions, booking_id)
        results = (
            await repo.cancel_booking(s1, tap1, refund=True),
            await repo.cancel_booking(s2, tap2, refund=True),
        )
        await s1.close()
        await s2.close()
        return results, tap2.status, tap2.refund_owed

    assert run(scenario) == ((True, False), BookingStatus.CANCELLED, True)


def test_releasing_a_hold_loses_to_a_payment_that_came_first(run):
    async def scenario(sessions):
        booking_id = await add(sessions)
        session, seen = await load(sessions, booking_id)  # the client saw an unpaid hold
        async with sessions() as payment:
            await repo.activate_paid(payment, await payment.get(Booking, booking_id), "A")
        cancelled = await repo.cancel_booking(session, seen, refund=False)
        await session.close()
        return cancelled, seen.status

    # Otherwise a paid booking would be cancelled without a refund
    assert run(scenario) == (False, BookingStatus.ACTIVE)


def test_retry_never_touches_a_deposit_kept_after_late_cancellation(run):
    async def scenario(sessions):
        # Like the one in the live DB: cancelled, paid, not refunded, cancelled < 24 h ahead
        await add(sessions, status=BookingStatus.CANCELLED, payment_charge_id="kept")
        owed_id = await add(sessions, status=BookingStatus.ACTIVE, payment_charge_id="A")
        async with sessions() as session:
            await repo.cancel_booking(session, await session.get(Booking, owed_id), refund=True)
            return [b.payment_charge_id for b in await repo.owed_refunds(session)]

    assert run(scenario) == ["A"]


def test_first_language_insert_doesnt_fail_on_a_second_update(run):
    async def scenario(sessions):
        async with sessions() as first, sessions() as second:
            await repo.save_new_lang(first, 9, "en")
            await repo.save_new_lang(second, 9, "uk")  # the user's second update, at once
            return await repo.get_lang(first, 9)

    assert run(scenario) == "en"

"""All database queries of the bot live here."""

from datetime import datetime, time

from sqlalchemy import ColumnElement, select, text, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from slotbook.models import Booking, BookingStatus, Service, Setting, UserPrefs, WorkDay
from slotbook.texts import TEXTS, Ru

DEPOSIT_KEY = "deposit_stars"
# Integer primary keys are 32-bit: a bigger id from forged callback data or an invoice payload
# would make the driver raise instead of finding nothing
MAX_ID = 2**31 - 1

DEMO_SERVICES = [("Стрижка", 60, 1500), ("Стрижка бороды", 30, 800), ("Стрижка + борода", 90, 2000)]
DEMO_HOURS = {0: (10, 20), 1: (10, 20), 2: (10, 20), 3: (10, 20), 4: (10, 20), 5: (11, 17)}


async def seed_defaults(session: AsyncSession) -> None:
    """Fill an empty DB with demo services and hours so the bot works right after start."""
    if await session.scalar(select(Service.id).limit(1)) is None:
        session.add_all(Service(name=n, duration_min=d, price=p) for n, d, p in DEMO_SERVICES)
    if await session.scalar(select(WorkDay.weekday).limit(1)) is None:
        for wd in range(7):
            hours = DEMO_HOURS.get(wd)
            session.add(
                WorkDay(
                    weekday=wd,
                    start=time(hours[0]) if hours else None,
                    end=time(hours[1]) if hours else None,
                )
            )
    await session.commit()


# --- Services ---


async def active_services(session: AsyncSession) -> list[Service]:
    result = await session.scalars(select(Service).where(Service.is_active).order_by(Service.price))
    return list(result)


async def get_service(session: AsyncSession, service_id: int) -> Service | None:
    if not 0 < service_id <= MAX_ID:
        return None
    return await session.get(Service, service_id)


async def add_service(session: AsyncSession, name: str, duration_min: int, price: int) -> None:
    session.add(Service(name=name, duration_min=duration_min, price=price))
    await session.commit()


async def hide_service(session: AsyncSession, service_id: int) -> None:
    service = await get_service(session, service_id)
    if service:
        service.is_active = False
        await session.commit()


# --- Language ---


async def get_lang(session: AsyncSession, user_id: int) -> str | None:
    prefs = await session.get(UserPrefs, user_id)
    return prefs.lang if prefs else None


async def set_lang(session: AsyncSession, user_id: int, lang: str) -> None:
    await session.merge(UserPrefs(id=user_id, lang=lang))
    await session.commit()


async def save_new_lang(session: AsyncSession, user_id: int, lang: str) -> None:
    """Store a new user's language. Their first two updates may arrive at once: the second
    insert is skipped instead of failing on the primary key."""
    await session.execute(
        pg_insert(UserPrefs).values(id=user_id, lang=lang).on_conflict_do_nothing()
    )
    await session.commit()


async def texts_for(session: AsyncSession, user_id: int) -> Ru:
    """Texts for messages the bot sends on its own (reminders, notifications)."""
    return TEXTS[await get_lang(session, user_id) or "ru"]


# --- Settings ---


async def get_deposit(session: AsyncSession) -> int:
    """Deposit in Telegram Stars the client pays when booking; 0 = no prepayment."""
    setting = await session.get(Setting, DEPOSIT_KEY)
    return int(setting.value) if setting else 0


async def set_deposit(session: AsyncSession, stars: int) -> None:
    await session.merge(Setting(key=DEPOSIT_KEY, value=str(stars)))
    await session.commit()


# --- Working hours ---


async def work_days(session: AsyncSession) -> dict[int, WorkDay]:
    return {wd.weekday: wd for wd in await session.scalars(select(WorkDay))}


async def set_work_day(
    session: AsyncSession, weekday: int, start: time | None, end: time | None
) -> None:
    await session.merge(WorkDay(weekday=weekday, start=start, end=end))
    await session.commit()


# --- Bookings ---


async def lock_bookings(session: AsyncSession) -> None:
    """Serialize booking creation so two clients can't grab the same slot at once.
    The lock is held until the transaction ends."""
    if session.bind.dialect.name == "postgresql":
        await session.execute(text("SELECT pg_advisory_xact_lock(1001)"))


async def busy_intervals(
    session: AsyncSession, start: datetime, end: datetime
) -> list[tuple[datetime, datetime]]:
    rows = await session.execute(
        select(Booking.starts_at, Booking.ends_at).where(
            # A booking waiting for the deposit holds its slot too
            Booking.status.in_(BookingStatus.OPEN),
            Booking.starts_at < end,
            Booking.ends_at > start,
        )
    )
    return [(s, e) for s, e in rows]


async def get_booking(session: AsyncSession, booking_id: int) -> Booking | None:
    if not 0 < booking_id <= MAX_ID:
        return None
    return await session.get(Booking, booking_id)


async def bookings_between(session: AsyncSession, start: datetime, end: datetime) -> list[Booking]:
    """Confirmed bookings and holds waiting for the deposit, for the master's list."""
    result = await session.scalars(
        select(Booking)
        .where(
            Booking.status.in_(BookingStatus.OPEN),
            Booking.starts_at >= start,
            Booking.starts_at < end,
        )
        .order_by(Booking.starts_at)
    )
    return list(result)


async def upcoming_user_bookings(
    session: AsyncSession, user_id: int, now: datetime
) -> list[Booking]:
    """The client's upcoming bookings: confirmed ones and holds waiting for the deposit."""
    result = await session.scalars(
        select(Booking)
        .where(
            Booking.user_id == user_id,
            Booking.status.in_(BookingStatus.OPEN),
            Booking.starts_at > now,
        )
        .order_by(Booking.starts_at)
    )
    return list(result)


# Status changes below are single conditional UPDATEs: a payment, the expiry job and button
# presses run concurrently, and only one of them may move a booking on from a given status.


async def _change(
    session: AsyncSession, booking: Booking, *where: ColumnElement[bool], **values: object
) -> bool:
    """UPDATE the booking if it still matches `where`; reload it either way, so the caller
    sees what actually happened. False if another update got there first."""
    result = await session.execute(
        update(Booking)
        .where(Booking.id == booking.id, *where)
        .values(**values)
        .returning(Booking.id)
        .execution_options(synchronize_session=False)
    )
    await session.commit()
    await session.refresh(booking)
    return result.first() is not None


async def cancel_booking(session: AsyncSession, booking: Booking, refund: bool) -> bool:
    """Cancel a booking that is still in the status the caller saw. With `refund` the deposit
    is marked as owed back in the same UPDATE, so it can't be forgotten if the refund fails."""
    return await _change(
        session,
        booking,
        Booking.status == booking.status,
        status=BookingStatus.CANCELLED,
        refund_owed=refund,
    )


async def activate_paid(session: AsyncSession, booking: Booking, charge_id: str) -> bool:
    """Confirm a held booking once its deposit is paid. False if it no longer waits for
    payment: the hold was released, or another payment was already counted."""
    return await _change(
        session,
        booking,
        Booking.status == BookingStatus.PENDING,
        status=BookingStatus.ACTIVE,
        payment_charge_id=charge_id,
    )


async def record_late_payment(session: AsyncSession, booking: Booking, charge_id: str) -> bool:
    """A payment that came after the hold was released: keep its charge id on the booking and
    mark it as owed back. False if the booking already has a payment."""
    return await _change(
        session,
        booking,
        Booking.payment_charge_id.is_(None),
        payment_charge_id=charge_id,
        refund_owed=True,
    )


async def expire_unpaid(session: AsyncSession, created_before: datetime) -> list[Booking]:
    """Release slots held for deposits that weren't paid in time. Only bookings still
    PENDING at the moment of the UPDATE expire, so one paid at the same time stays active."""
    expired_ids = list(
        await session.scalars(
            update(Booking)
            .where(Booking.status == BookingStatus.PENDING, Booking.created_at < created_before)
            .values(status=BookingStatus.EXPIRED)
            .returning(Booking.id)
            .execution_options(synchronize_session=False)
        )
    )
    await session.commit()
    if not expired_ids:
        return []
    return list(
        await session.scalars(
            select(Booking)
            .where(Booking.id.in_(expired_ids))
            .execution_options(populate_existing=True)
        )
    )


async def owed_refunds(session: AsyncSession) -> list[Booking]:
    """Bookings whose payment must go back but the refund hasn't gone through yet."""
    return list(await session.scalars(select(Booking).where(Booking.refund_owed)))

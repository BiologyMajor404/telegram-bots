"""All database queries of the bot live here."""

from datetime import datetime, time

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from slotbook.models import Booking, BookingStatus, Service, WorkDay

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
    return await session.get(Service, service_id)


async def add_service(session: AsyncSession, name: str, duration_min: int, price: int) -> None:
    session.add(Service(name=name, duration_min=duration_min, price=price))
    await session.commit()


async def hide_service(session: AsyncSession, service_id: int) -> None:
    service = await session.get(Service, service_id)
    if service:
        service.is_active = False
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
            Booking.status == BookingStatus.ACTIVE,
            Booking.starts_at < end,
            Booking.ends_at > start,
        )
    )
    return [(s, e) for s, e in rows]


async def get_booking(session: AsyncSession, booking_id: int) -> Booking | None:
    return await session.get(Booking, booking_id)


async def bookings_between(session: AsyncSession, start: datetime, end: datetime) -> list[Booking]:
    result = await session.scalars(
        select(Booking)
        .where(
            Booking.status == BookingStatus.ACTIVE,
            Booking.starts_at >= start,
            Booking.starts_at < end,
        )
        .order_by(Booking.starts_at)
    )
    return list(result)


async def upcoming_user_bookings(
    session: AsyncSession, user_id: int, now: datetime
) -> list[Booking]:
    result = await session.scalars(
        select(Booking)
        .where(
            Booking.user_id == user_id,
            Booking.status == BookingStatus.ACTIVE,
            Booking.starts_at > now,
        )
        .order_by(Booking.starts_at)
    )
    return list(result)


async def cancel_booking(session: AsyncSession, booking: Booking) -> None:
    booking.status = BookingStatus.CANCELLED
    await session.commit()

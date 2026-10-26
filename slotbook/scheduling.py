"""Booking logic on top of the DB: free days/slots and creating a booking safely."""

from datetime import UTC, date, datetime, timedelta
from zoneinfo import ZoneInfo

from aiogram.types import User
from sqlalchemy.ext.asyncio import AsyncSession

from slotbook import repo
from slotbook.models import Booking, BookingStatus, Service
from slotbook.slots import available_slots

BOOKING_HORIZON_DAYS = 14
# Upcoming bookings (paid or waiting for payment) one client may hold at once
MAX_OPEN_BOOKINGS = 3


class BookingLimitError(Exception):
    """The client already holds MAX_OPEN_BOOKINGS upcoming bookings."""


def now_utc() -> datetime:
    return datetime.now(UTC)


async def free_slots_by_day(
    session: AsyncSession, service: Service, tz: ZoneInfo, days: list[date]
) -> dict[date, list[datetime]]:
    """Free slots for each of `days` with a single DB query for busy intervals."""
    if not days:
        return {}
    hours = await repo.work_days(session)
    range_start = datetime.combine(days[0], datetime.min.time(), tzinfo=tz)
    range_end = datetime.combine(days[-1] + timedelta(days=1), datetime.min.time(), tzinfo=tz)
    busy = await repo.busy_intervals(session, range_start, range_end)
    now = now_utc()
    duration = timedelta(minutes=service.duration_min)

    result = {}
    for day in days:
        wd = hours.get(day.weekday())
        day_hours = (wd.start, wd.end) if wd and wd.start and wd.end else None
        result[day] = available_slots(day, day_hours, duration, busy, now, tz)
    return result


async def free_days(session: AsyncSession, service: Service, tz: ZoneInfo) -> list[date]:
    today = now_utc().astimezone(tz).date()
    days = [today + timedelta(days=i) for i in range(BOOKING_HORIZON_DAYS)]
    slots = await free_slots_by_day(session, service, tz, days)
    return [d for d in days if slots[d]]


async def free_slots(
    session: AsyncSession, service: Service, tz: ZoneInfo, day: date
) -> list[datetime]:
    return (await free_slots_by_day(session, service, tz, [day]))[day]


async def book(
    session: AsyncSession,
    service: Service,
    starts_at: datetime,
    user: User,
    tz: ZoneInfo,
    deposit: int = 0,
) -> Booking | None:
    """Create a booking or return None if the slot is no longer free (or outside the booking
    window). Raises BookingLimitError if the client already has too many open bookings.
    With a deposit the booking stays PENDING (slot held) until the client pays."""
    await repo.lock_bookings(session)
    # Checked under the lock: the slot comes from client-controlled callback data, and
    # parallel button presses must not slip past the per-client limit
    now = now_utc()
    day = starts_at.astimezone(tz).date()
    if day >= now.astimezone(tz).date() + timedelta(days=BOOKING_HORIZON_DAYS):
        await session.rollback()
        return None
    if await repo.count_open_bookings(session, user.id, now) >= MAX_OPEN_BOOKINGS:
        await session.rollback()
        raise BookingLimitError
    if starts_at not in await free_slots(session, service, tz, day):
        await session.rollback()
        return None

    until_start = starts_at - now_utc()
    booking = Booking(
        user_id=user.id,
        user_name=user.full_name,
        username=user.username,
        service_id=service.id,
        starts_at=starts_at,
        ends_at=starts_at + timedelta(minutes=service.duration_min),
        status=BookingStatus.PENDING if deposit else BookingStatus.ACTIVE,
        deposit_stars=deposit,
        # Don't send a "tomorrow" reminder for a booking made a few hours ahead
        reminded_24h=until_start < timedelta(hours=24),
        reminded_2h=until_start < timedelta(hours=2),
    )
    session.add(booking)
    await session.commit()
    await session.refresh(booking, ["service"])
    return booking

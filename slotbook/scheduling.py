"""Booking logic on top of the DB: free days/slots and creating a booking safely."""

import math
from datetime import UTC, date, datetime, timedelta
from zoneinfo import ZoneInfo

from aiogram.types import User
from sqlalchemy.ext.asyncio import AsyncSession

from slotbook import repo
from slotbook.models import USER_NAME_LEN, Booking, BookingStatus, Service
from slotbook.slots import available_slots

BOOKING_HORIZON_DAYS = 14
# Upcoming bookings (paid or waiting for payment) one client may hold at once
MAX_OPEN_BOOKINGS = 3
# Cancelling a booking made less than FRESH_BOOKING ago (the master was told about it twice),
# or letting a deposit hold expire, makes the client wait REBOOK_COOLDOWN before booking again.
# Stops book-and-cancel loops that spam the master and holds re-taken just to block a slot
FRESH_BOOKING = timedelta(hours=1)
REBOOK_COOLDOWN = timedelta(minutes=5)

# user id -> when their cooldown started. In memory: losing it on restart is harmless
_cooldown_from: dict[int, datetime] = {}


class CantBookError(Exception):
    """This client may not book the slot right now."""


class AlreadyBookedError(CantBookError):
    """The client already holds this very slot: a second tap on Confirm."""


class BookingLimitError(CantBookError):
    """The client already holds MAX_OPEN_BOOKINGS upcoming bookings."""


class HoldExistsError(CantBookError):
    """The client already holds a slot waiting for the deposit; one at a time."""


class RebookCooldownError(CantBookError):
    """The client cancelled a fresh booking or let a hold expire a moment ago."""

    def __init__(self, left: timedelta) -> None:
        super().__init__(left)
        self.minutes = max(1, math.ceil(left.total_seconds() / 60))


def now_utc() -> datetime:
    return datetime.now(UTC)


def bookable_day(day: date, tz: ZoneInfo) -> bool:
    """From today up to the booking horizon. Days come from callback data, so anything else
    (an old button, a forged value) must not reach the slot math."""
    today = now_utc().astimezone(tz).date()
    return today <= day < today + timedelta(days=BOOKING_HORIZON_DAYS)


def start_cooldown(user_id: int, now: datetime) -> None:
    for uid, since in list(_cooldown_from.items()):
        if now - since >= REBOOK_COOLDOWN:
            del _cooldown_from[uid]
    _cooldown_from[user_id] = now


def cooldown_left(user_id: int, now: datetime) -> timedelta | None:
    since = _cooldown_from.get(user_id)
    if since is None or now - since >= REBOOK_COOLDOWN:
        return None
    return REBOOK_COOLDOWN - (now - since)


def cancel_starts_cooldown(booking: Booking, now: datetime) -> bool:
    """A confirmed booking cancelled by the client soon after it was made. Releasing a hold
    doesn't count: the master never heard of it, and it's how a client picks another time."""
    return booking.status == BookingStatus.ACTIVE and now - booking.created_at < FRESH_BOOKING


def check_client(
    mine: list[Booking],
    service_id: int,
    starts_at: datetime,
    deposit: int,
    cooldown: timedelta | None,
) -> None:
    """Raise a CantBookError if the client may not book this slot now. `mine` are their
    upcoming bookings, confirmed or waiting for the deposit."""
    if any(b.service_id == service_id and b.starts_at == starts_at for b in mine):
        raise AlreadyBookedError
    if cooldown:
        raise RebookCooldownError(cooldown)
    if len(mine) >= MAX_OPEN_BOOKINGS:
        raise BookingLimitError
    if deposit and any(b.status == BookingStatus.PENDING for b in mine):
        raise HoldExistsError


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


async def _release_lock(session: AsyncSession) -> None:
    """End the transaction, and with it the booking lock, when nothing was written. Commit,
    not rollback: rollback would expire the objects the caller goes on using (the service),
    and reading them again outside a DB call fails in async SQLAlchemy."""
    await session.commit()


async def book(
    session: AsyncSession,
    service: Service,
    starts_at: datetime,
    user: User,
    tz: ZoneInfo,
    deposit: int = 0,
) -> Booking | None:
    """Create a booking or return None if the slot is no longer free (or outside the booking
    window). Raises a CantBookError if the client may not book now (see check_client).
    With a deposit the booking stays PENDING (slot held) until the client pays."""
    await repo.lock_bookings(session)
    # Checked under the lock: the slot comes from client-controlled callback data, and
    # parallel button presses must not slip past the per-client limits
    now = now_utc()
    mine = await repo.upcoming_user_bookings(session, user.id, now)
    try:
        check_client(mine, service.id, starts_at, deposit, cooldown_left(user.id, now))
    except CantBookError:
        await _release_lock(session)
        raise
    day = starts_at.astimezone(tz).date()
    if not bookable_day(day, tz) or starts_at not in await free_slots(session, service, tz, day):
        await _release_lock(session)
        return None

    until_start = starts_at - now_utc()
    booking = Booking(
        user_id=user.id,
        user_name=user.full_name[:USER_NAME_LEN],
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

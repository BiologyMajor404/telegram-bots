"""Pure slot math, no DB or Telegram here, so it's easy to unit-test."""

from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

SLOT_STEP = timedelta(minutes=30)
# How long before a slot the client can still book it
MIN_LEAD_TIME = timedelta(hours=1)

Interval = tuple[datetime, datetime]


def overlaps(a: Interval, b: Interval) -> bool:
    return a[0] < b[1] and b[0] < a[1]


def available_slots(
    day: date,
    hours: tuple[time, time] | None,
    duration: timedelta,
    busy: list[Interval],
    now: datetime,
    tz: ZoneInfo,
    step: timedelta = SLOT_STEP,
    min_lead: timedelta = MIN_LEAD_TIME,
) -> list[datetime]:
    """Start times on `day` where a service of `duration` fits into working hours
    without overlapping `busy` intervals and not earlier than now + min_lead."""
    if hours is None:
        return []
    start = datetime.combine(day, hours[0], tzinfo=tz)
    end = datetime.combine(day, hours[1], tzinfo=tz)
    earliest = now + min_lead

    result = []
    t = start
    while t + duration <= end:
        if t >= earliest and not any(overlaps((t, t + duration), b) for b in busy):
            result.append(t)
        t += step
    return result

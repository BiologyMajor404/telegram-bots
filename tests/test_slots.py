from datetime import UTC, date, datetime, time, timedelta
from zoneinfo import ZoneInfo

import pytest

from slotbook.handlers.admin import parse_hours
from slotbook.keyboards import day_to_int, int_to_day
from slotbook.slots import available_slots

TZ = ZoneInfo("Europe/Moscow")
DAY = date(2026, 11, 2)  # Monday
HOURS = (time(10), time(13))
HOUR = timedelta(hours=1)
# "now" far before DAY so lead time doesn't interfere
EARLY = datetime(2026, 11, 1, tzinfo=UTC)


def at(h: int, m: int = 0) -> datetime:
    return datetime.combine(DAY, time(h, m), tzinfo=TZ)


def hhmm(slots: list[datetime]) -> list[str]:
    return [s.strftime("%H:%M") for s in slots]


def test_empty_day_gives_slots_every_30_min():
    slots = available_slots(DAY, HOURS, HOUR, [], EARLY, TZ)
    assert hhmm(slots) == ["10:00", "10:30", "11:00", "11:30", "12:00"]


def test_day_off_has_no_slots():
    assert available_slots(DAY, None, HOUR, [], EARLY, TZ) == []


def test_service_must_fit_before_closing():
    slots = available_slots(DAY, HOURS, timedelta(hours=3), [], EARLY, TZ)
    assert hhmm(slots) == ["10:00"]


def test_busy_interval_blocks_overlapping_slots():
    busy = [(at(11), at(12))]
    slots = available_slots(DAY, HOURS, HOUR, busy, EARLY, TZ)
    # 10:30 would end at 11:30 and 11:30 overlaps too; 12:00 starts right when busy ends
    assert hhmm(slots) == ["10:00", "12:00"]


def test_slots_too_close_to_now_are_hidden():
    now = at(10, 15)  # min lead time is 1 hour -> earliest 11:15
    slots = available_slots(DAY, HOURS, timedelta(minutes=30), [], now, TZ)
    assert hhmm(slots) == ["11:30", "12:00", "12:30"]


def test_busy_in_other_timezone_is_compared_correctly():
    # 08:00 UTC == 11:00 Moscow
    busy = [(datetime(2026, 11, 2, 8, tzinfo=UTC), datetime(2026, 11, 2, 9, tzinfo=UTC))]
    slots = available_slots(DAY, HOURS, HOUR, busy, EARLY, TZ)
    assert hhmm(slots) == ["10:00", "12:00"]


def test_day_callback_roundtrip():
    assert int_to_day(day_to_int(DAY)) == DAY


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("10:00-19:00", (time(10), time(19))),
        ("9:30 - 18:00", (time(9, 30), time(18))),
        ("-", None),
    ],
)
def test_parse_hours(raw, expected):
    assert parse_hours(raw) == expected


@pytest.mark.parametrize("raw", ["19:00-10:00", "10-19", "abc", "25:00-26:00"])
def test_parse_hours_rejects_bad_input(raw):
    with pytest.raises(ValueError):
        parse_hours(raw)

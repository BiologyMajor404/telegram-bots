"""SlotBook booking rules: limits, double taps, cooldown, odd callback data, book()."""

import asyncio
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from zoneinfo import ZoneInfo

import pytest

from slotbook import keyboards as kb
from slotbook import repo, scheduling
from slotbook.models import USER_NAME_LEN, BookingStatus

TZ = ZoneInfo("Europe/Moscow")
NOW = datetime(2026, 11, 2, 9, tzinfo=UTC)  # 12:00 in Moscow
SLOT = NOW + timedelta(days=1)


def bk(starts_at=SLOT, service_id=1, status=BookingStatus.ACTIVE, created_ago=timedelta(days=1)):
    return SimpleNamespace(
        starts_at=starts_at, service_id=service_id, status=status, created_at=NOW - created_ago
    )


@pytest.fixture(autouse=True)
def fixed_clock(monkeypatch):
    monkeypatch.setattr(scheduling, "now_utc", lambda: NOW)
    monkeypatch.setattr(scheduling, "_cooldown_from", {})


# --- check_client ---


def test_free_client_may_book():
    scheduling.check_client([], 1, SLOT, deposit=50, cooldown=None)


def test_second_tap_on_confirm_is_recognised_first():
    # Even at the limit and in a cooldown: it's the same booking, not a new one
    mine = [bk(), bk(SLOT + timedelta(days=1)), bk(SLOT + timedelta(days=2))]
    with pytest.raises(scheduling.AlreadyBookedError):
        scheduling.check_client(mine, 1, SLOT, 0, cooldown=timedelta(minutes=1))


def test_same_time_other_service_is_not_a_double_tap():
    with pytest.raises(scheduling.BookingLimitError):
        scheduling.check_client([bk(), bk(), bk()], 2, SLOT, 0, None)


def test_open_bookings_are_limited():
    mine = [bk(SLOT + timedelta(days=i)) for i in range(1, scheduling.MAX_OPEN_BOOKINGS + 1)]
    with pytest.raises(scheduling.BookingLimitError):
        scheduling.check_client(mine, 1, SLOT, 0, None)


def test_only_one_hold_waiting_for_the_deposit():
    mine = [bk(SLOT + timedelta(days=1), status=BookingStatus.PENDING)]
    with pytest.raises(scheduling.HoldExistsError):
        scheduling.check_client(mine, 1, SLOT, deposit=50, cooldown=None)
    # Without a deposit the new booking is no hold, so the rule doesn't apply
    scheduling.check_client(mine, 1, SLOT, deposit=0, cooldown=None)


def test_cooldown_blocks_and_rounds_minutes_up():
    with pytest.raises(scheduling.RebookCooldownError) as e:
        scheduling.check_client([], 1, SLOT, 0, cooldown=timedelta(minutes=4, seconds=1))
    assert e.value.minutes == 5


# --- Cooldown ---


def test_cooldown_lasts_rebook_cooldown():
    scheduling.start_cooldown(7, NOW)
    assert scheduling.cooldown_left(7, NOW + timedelta(minutes=1)) == (
        scheduling.REBOOK_COOLDOWN - timedelta(minutes=1)
    )
    assert scheduling.cooldown_left(7, NOW + scheduling.REBOOK_COOLDOWN) is None
    assert scheduling.cooldown_left(8, NOW) is None


def test_old_cooldowns_are_forgotten():
    scheduling.start_cooldown(7, NOW)
    scheduling.start_cooldown(8, NOW + scheduling.REBOOK_COOLDOWN)
    assert set(scheduling._cooldown_from) == {8}


@pytest.mark.parametrize(
    ("status", "created_ago", "expected"),
    [
        (BookingStatus.ACTIVE, timedelta(minutes=10), True),  # book-and-cancel loop
        (BookingStatus.ACTIVE, timedelta(days=2), False),  # an old booking moved to another day
        (BookingStatus.PENDING, timedelta(minutes=10), False),  # releasing a hold
    ],
)
def test_which_cancellations_start_a_cooldown(status, created_ago, expected):
    booking = bk(status=status, created_ago=created_ago)
    assert scheduling.cancel_starts_cooldown(booking, NOW) is expected


# --- Days and callback data ---


@pytest.mark.parametrize(
    ("offset", "expected"),
    [
        (-1, False),
        (0, True),
        (scheduling.BOOKING_HORIZON_DAYS - 1, True),
        (scheduling.BOOKING_HORIZON_DAYS, False),
    ],
)
def test_bookable_days(offset, expected):
    today = NOW.astimezone(TZ).date()
    assert scheduling.bookable_day(today + timedelta(days=offset), TZ) is expected


@pytest.mark.parametrize("value", [20261399, 20260230, 0, -5, 10**30])
def test_forged_day_is_rejected(value):
    assert kb.int_to_day(value) is None


@pytest.mark.parametrize("ts", [-1, 2**32, 10**20])
def test_forged_timestamp_is_rejected(ts):
    assert kb.ts_to_dt(ts) is None


def test_slot_timestamp_roundtrip():
    assert kb.ts_to_dt(int(SLOT.timestamp())) == SLOT


@pytest.mark.parametrize("bad_id", [0, -1, 2**31, 10**20])
def test_ids_out_of_range_are_not_looked_up(bad_id):
    class NoSession:
        async def get(self, *args):
            raise AssertionError("must not reach the DB")

    assert asyncio.run(repo.get_booking(NoSession(), bad_id)) is None
    assert asyncio.run(repo.get_service(NoSession(), bad_id)) is None


# --- book() ---


class FakeSession:
    def __init__(self):
        self.calls = []
        self.added = []

    def add(self, obj):
        self.added.append(obj)

    async def commit(self):
        self.calls.append("commit")

    async def rollback(self):
        self.calls.append("rollback")

    async def refresh(self, obj, attrs=None):
        self.calls.append("refresh")


SERVICE = SimpleNamespace(id=1, duration_min=60)
USER = SimpleNamespace(id=7, full_name="Я" * 129, username=None)


def run_book(monkeypatch, starts_at=SLOT, mine=(), free=None, deposit=0):
    """book() with the DB faked; `free` are the free slots (default: the requested one)."""

    async def no_lock(session):
        pass

    async def upcoming(session, user_id, now):
        return list(mine)

    async def free_slots(session, service, tz, day):
        return [starts_at] if free is None else free

    monkeypatch.setattr(repo, "lock_bookings", no_lock)
    monkeypatch.setattr(repo, "upcoming_user_bookings", upcoming)
    monkeypatch.setattr(scheduling, "free_slots", free_slots)
    session = FakeSession()
    try:
        result = asyncio.run(scheduling.book(session, SERVICE, starts_at, USER, TZ, deposit))
    except scheduling.CantBookError as e:
        result = e
    return session, result


def test_taken_slot_ends_the_transaction_without_rollback(monkeypatch):
    # A rollback expires the loaded service, and the handler's "pick another time" list
    # then crashed reading service.duration_min (MissingGreenlet)
    session, result = run_book(monkeypatch, free=[])
    assert result is None
    assert session.calls == ["commit"]


def test_refusal_ends_the_transaction_without_rollback(monkeypatch):
    mine = [bk(SLOT + timedelta(days=i)) for i in range(1, scheduling.MAX_OPEN_BOOKINGS + 1)]
    session, result = run_book(monkeypatch, mine=mine)
    assert isinstance(result, scheduling.BookingLimitError)
    assert session.calls == ["commit"]
    assert session.added == []


def test_slot_beyond_the_horizon_is_refused(monkeypatch):
    session, result = run_book(monkeypatch, SLOT + timedelta(days=scheduling.BOOKING_HORIZON_DAYS))
    assert result is None
    assert session.calls == ["commit"]
    assert session.added == []


def test_longest_telegram_name_fits_the_column(monkeypatch):
    _, booking = run_book(monkeypatch, deposit=50)
    assert len(booking.user_name) == USER_NAME_LEN
    assert booking.status == BookingStatus.PENDING
    assert booking.deposit_stars == 50

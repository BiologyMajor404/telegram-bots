"""SlotBook texts: alert lengths, how bookings are shown, language of new users."""

import asyncio
from datetime import UTC, datetime
from types import SimpleNamespace
from zoneinfo import ZoneInfo

import pytest

from slotbook import i18n, repo
from slotbook.models import BookingStatus
from slotbook.texts import TEXTS, short

TZ = ZoneInfo("Europe/Moscow")
# Telegram shows at most 200 characters in a callback answer
ALERT_LIMIT = 200
ALERTS = {
    "NO_SERVICES": {},
    "NO_DAYS": {},
    "NO_TIME": {},
    "SLOT_TAKEN": {},
    "TOO_MANY_BOOKINGS": {"limit": 3},
    "HOLD_EXISTS": {},
    "REBOOK_COOLDOWN": {"minutes": 5},
    "CANT_CANCEL": {},
    "CANCELLED": {},
    "CANCELLED_REFUNDED": {},
    "CANCELLED_REFUND_PENDING": {},
    "CANCELLED_NO_REFUND": {},
}


@pytest.mark.parametrize("lang", list(TEXTS))
def test_alerts_fit_a_callback_answer(lang):
    t = TEXTS[lang]
    too_long = [
        name for name, args in ALERTS.items() if len(getattr(t, name).format(**args)) > ALERT_LIMIT
    ]
    assert not too_long


def booking(status=BookingStatus.ACTIVE, charge=None, refunded=False):
    return SimpleNamespace(
        starts_at=datetime(2026, 11, 2, 9, tzinfo=UTC),
        service=SimpleNamespace(name="Cut", duration_min=60, price=100),
        status=status,
        payment_charge_id=charge,
        refunded=refunded,
        deposit_stars=50,
    )


@pytest.mark.parametrize(
    ("b", "line"),
    [
        (booking(BookingStatus.PENDING), "DEPOSIT_AWAITED"),
        (booking(charge="A"), "DEPOSIT_PAID"),
        (booking(charge="A", refunded=True), None),
        (booking(), None),
    ],
)
def test_booking_shows_its_deposit(b, line):
    t = TEXTS["en"]
    text = t.fmt_booking(b, TZ)
    for name in ("DEPOSIT_AWAITED", "DEPOSIT_PAID"):
        assert (getattr(t, name).format(stars=50) in text) is (name == line)


def test_short_cuts_only_long_names():
    assert short("Ann", 3) == "Ann"
    assert short("Annabel", 4) == "Ann…"


# --- Language of a new user ---


def lang_data(chat_type, language_code="uk"):
    return {
        "event_from_user": SimpleNamespace(id=7, language_code=language_code),
        "event_chat": SimpleNamespace(type=chat_type),
        "session": None,
    }


def test_group_messages_dont_touch_the_db(monkeypatch):
    async def no_db(*args):
        raise AssertionError("must not reach the DB")

    monkeypatch.setattr(repo, "get_lang", no_db)
    assert asyncio.run(i18n.resolve_lang(lang_data("supergroup"))) == "uk"


def test_new_user_language_is_stored_without_conflicts(monkeypatch):
    saved = []

    async def get_lang(session, user_id):
        return None

    async def save_new_lang(session, user_id, lang):
        saved.append((user_id, lang))

    monkeypatch.setattr(repo, "get_lang", get_lang)
    monkeypatch.setattr(repo, "save_new_lang", save_new_lang)
    assert asyncio.run(i18n.resolve_lang(lang_data("private", "pl"))) == "pl"
    assert saved == [(7, "pl")]

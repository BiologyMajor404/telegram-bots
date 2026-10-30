"""ChatGuard Pro payments: subscription dates and payloads."""

from datetime import UTC, datetime, timedelta

from chatguard.handlers.payments import (
    already_paid,
    parse_pro_payload,
    pro_payload,
    subscription_end,
)
from chatguard.models import Chat


def test_subscription_end_from_unix_timestamp():
    # This is what Telegram actually sends (a payment once crashed on it)
    assert subscription_end(1_795_480_116) == datetime.fromtimestamp(1_795_480_116, UTC)


def test_subscription_end_from_datetime_and_missing():
    naive = datetime(2026, 11, 24, 0, 48)
    assert subscription_end(naive).tzinfo is not None
    fallback = subscription_end(None)
    assert timedelta(days=29) < fallback - datetime.now(UTC) <= timedelta(days=30)


def test_pro_payload_roundtrip():
    assert parse_pro_payload(pro_payload(-1004354426627)) == -1004354426627
    assert parse_pro_payload("pro:abc") is None and parse_pro_payload("x") is None


def test_second_subscription_is_refused_while_pro_runs():
    now = datetime.now(UTC)
    assert not already_paid(Chat(pro_until=None), now)
    assert not already_paid(Chat(pro_until=now - timedelta(days=3)), now)  # expired
    assert already_paid(Chat(pro_until=now + timedelta(days=20)), now)
    # In the last day a payment may be the renewal itself
    assert not already_paid(Chat(pro_until=now + timedelta(hours=20)), now)

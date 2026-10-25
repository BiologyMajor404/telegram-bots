"""ChatGuard Pro payments: subscription dates and payloads."""

from datetime import UTC, datetime, timedelta

from chatguard.handlers.payments import parse_pro_payload, pro_payload, subscription_end


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

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import pytest

from slotbook.payments import invoice_payload, is_paid, parse_payload, refund_due

NOW = datetime(2026, 11, 2, 12, tzinfo=UTC)


def booking(hours_before: float, charge_id: str | None = "ch_1", refunded: bool = False):
    return SimpleNamespace(
        starts_at=NOW + timedelta(hours=hours_before),
        payment_charge_id=charge_id,
        refunded=refunded,
    )


def test_payload_roundtrip():
    assert parse_payload(invoice_payload(42)) == 42


@pytest.mark.parametrize("payload", ["", "booking:", "booking:abc", "other:1", "42"])
def test_parse_payload_rejects_garbage(payload):
    assert parse_payload(payload) is None


def test_unpaid_booking_is_never_refunded():
    assert not refund_due(booking(48, charge_id=None), NOW, by_master=True)


def test_already_refunded_is_not_paid():
    assert not is_paid(booking(48, refunded=True))


def test_client_cancelling_early_gets_refund():
    assert refund_due(booking(24), NOW, by_master=False)


def test_client_cancelling_late_keeps_no_refund():
    assert not refund_due(booking(23.5), NOW, by_master=False)


def test_master_cancelling_always_refunds():
    assert refund_due(booking(1), NOW, by_master=True)

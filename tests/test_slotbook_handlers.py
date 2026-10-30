"""SlotBook handlers with the DB and Telegram faked: what a payment, a cancellation and the
refund retry do, and what the client and the master are told."""

import asyncio
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from zoneinfo import ZoneInfo

import pytest
from aiogram.exceptions import TelegramBadRequest

from slotbook import payments, reminders, repo, scheduling
from slotbook.handlers import admin, client
from slotbook.handlers import payments as pay_handlers
from slotbook.models import BookingStatus
from slotbook.texts import TEXTS

T = TEXTS["en"]
TZ = ZoneInfo("Europe/Moscow")
NOW = datetime(2026, 11, 2, 9, tzinfo=UTC)
CLIENT_ID = 5


def booking(status=BookingStatus.ACTIVE, charge="A", hours_ahead=48, **fields):
    values = {
        "id": 1,
        "user_id": CLIENT_ID,
        "user_name": "Ann",
        "status": status,
        "payment_charge_id": charge,
        "refunded": False,
        "refund_owed": False,
        "deposit_stars": 50,
        "starts_at": NOW + timedelta(hours=hours_ahead),
        "created_at": NOW - timedelta(days=3),
        "service": SimpleNamespace(name="Cut", duration_min=60, price=100),
    } | fields
    return SimpleNamespace(**values)


class FakeMessage:
    def __init__(self, successful_payment=None):
        self.successful_payment = successful_payment
        self.sent = []

    async def answer(self, text, **kwargs):
        self.sent.append(text)

    async def edit_text(self, text, **kwargs):
        self.sent.append(text)


class FakeCallback:
    def __init__(self, user_id=CLIENT_ID):
        self.from_user = SimpleNamespace(id=user_id)
        self.message = FakeMessage()
        self.answers = []

    async def answer(self, text=None, show_alert=False):
        self.answers.append(text)


class Calls:
    """Replaces async functions with fakes that record their calls."""

    def __init__(self, monkeypatch):
        self.log = []
        self.monkeypatch = monkeypatch

    def fake(self, target, name, result=None, effect=None):
        """`target.name` returns `result`, after running `effect` with the same arguments."""

        async def replacement(*args, **kwargs):
            self.log.append((name, args, kwargs))
            if effect:
                effect(*args, **kwargs)
            return result

        self.monkeypatch.setattr(target, name, replacement)

    def called(self, name):
        return [c for c in self.log if c[0] == name]


@pytest.fixture
def calls(monkeypatch):
    c = Calls(monkeypatch)
    monkeypatch.setattr(scheduling, "now_utc", lambda: NOW)
    monkeypatch.setattr(scheduling, "_cooldown_from", {})
    notified = []

    async def notify(bot, session, admin_ids, build):
        notified.append(build(T))

    monkeypatch.setattr(pay_handlers, "notify_admins", notify)
    monkeypatch.setattr(client, "notify_admins", notify)
    c.notified = notified
    c.fake(payments, "alert_refund_failed")
    return c


# --- Payments ---


def pay(calls, bk, charge, activated=False, late=False, refunded=True):
    def activate(session, b, charge_id):
        b.status, b.payment_charge_id = BookingStatus.ACTIVE, charge_id

    def record_late(session, b, charge_id):
        b.payment_charge_id, b.refund_owed = charge_id, True

    calls.fake(repo, "get_booking", bk)
    calls.fake(repo, "activate_paid", activated, activate if activated else None)
    calls.fake(repo, "record_late_payment", late, record_late if late else None)
    calls.fake(payments, "refund", refunded)
    calls.fake(payments, "refund_charge", refunded)
    payment = SimpleNamespace(
        invoice_payload=payments.invoice_payload(bk.id),
        telegram_payment_charge_id=charge,
        total_amount=bk.deposit_stars,
    )
    message = FakeMessage(payment)
    asyncio.run(pay_handlers.successful_payment(message, None, TZ, None, {1}, T))
    return message.sent


def test_payment_confirms_the_hold(calls):
    sent = pay(calls, booking(BookingStatus.PENDING, charge=None), "A", activated=True)
    assert sent == [T.BOOKED.format(booking=T.fmt_booking(booking(charge="A"), TZ))]
    assert len(calls.notified) == 1
    assert not calls.called("refund") and not calls.called("refund_charge")


def test_redelivered_payment_is_ignored(calls):
    # The payment that confirmed the booking comes again: nothing is refunded or re-sent
    sent = pay(calls, booking(charge="A"), "A")
    assert sent == []
    assert not calls.called("refund") and not calls.called("refund_charge")
    assert calls.notified == []


def test_late_payment_is_refunded(calls):
    sent = pay(calls, booking(BookingStatus.EXPIRED, charge=None), "A", late=True)
    assert sent == [T.PAY_LATE_REFUNDED]
    assert not calls.called("alert_refund_failed")


def test_late_payment_refund_failure_is_not_reported_as_done(calls):
    bk = booking(BookingStatus.EXPIRED, charge=None)
    sent = pay(calls, bk, "A", late=True, refunded=False)
    assert sent == [T.PAY_LATE_REFUND_PENDING]
    assert bk.refund_owed  # the retry picks it up
    assert len(calls.called("alert_refund_failed")) == 1


def test_extra_payment_is_refunded_and_the_first_one_kept(calls):
    bk = booking(charge="A")
    sent = pay(calls, bk, "B")
    assert sent == [T.PAY_EXTRA_REFUNDED]
    assert [c[1][2] for c in calls.called("refund_charge")] == ["B"]
    assert not calls.called("refund")  # that one would give back the stored payment A
    assert bk.payment_charge_id == "A"
    assert not bk.refunded


def test_extra_payment_refund_failure_reaches_the_master(calls):
    sent = pay(calls, booking(charge="A"), "B", refunded=False)
    assert sent == [T.PAY_EXTRA_REFUND_FAILED]
    assert len(calls.notified) == 1
    assert "<code>B</code>" in calls.notified[0]


# --- Refunds ---


class FakeBot:
    def __init__(self, error=None):
        self.error = error
        self.refunds = []

    async def refund_star_payment(self, user_id, telegram_payment_charge_id):
        self.refunds.append(telegram_payment_charge_id)
        if self.error:
            raise TelegramBadRequest(method=None, message=self.error)


class FakeSession:
    async def commit(self):
        pass


@pytest.mark.parametrize(
    ("error", "ok"),
    [
        (None, True),
        # An earlier try went through but its answer was lost: the money is back
        ("Bad Request: CHARGE_ALREADY_REFUNDED", True),
        ("Bad Request: something else", False),
    ],
)
def test_refund_marks_the_booking(error, ok):
    bk = booking(refund_owed=True)
    assert asyncio.run(payments.refund(FakeBot(error), FakeSession(), bk)) is ok
    assert bk.refunded is ok
    assert bk.refund_owed is not ok


def test_retry_refunds_and_tells_only_those_refunded(calls, monkeypatch):
    done, failing = booking(id=1, user_id=11), booking(id=2, user_id=12)
    calls.fake(repo, "owed_refunds", [done, failing])
    calls.fake(repo, "texts_for", T)

    async def refund(bot, session, bk):
        return bk is done

    monkeypatch.setattr(payments, "refund", refund)
    sent = []

    async def safe_send(bot, chat_id, text, **kw):
        sent.append(chat_id)

    monkeypatch.setattr(reminders, "safe_send", safe_send)

    class Sessions:
        async def __aenter__(self):
            return None

        async def __aexit__(self, *exc):
            return False

    asyncio.run(reminders.retry_refunds(None, Sessions, TZ))
    assert sent == [11]


# --- Client cancels ---


def cancel(calls, bk, won=True, refunded=True, user_id=CLIENT_ID):
    def mark_cancelled(session, b, refund):
        b.status = BookingStatus.CANCELLED

    calls.fake(repo, "get_booking", bk)
    calls.fake(repo, "cancel_booking", won, mark_cancelled if won else None)
    calls.fake(repo, "upcoming_user_bookings", [])
    calls.fake(payments, "refund", refunded)
    cb = FakeCallback(user_id)
    asyncio.run(client.cancel_booking(cb, SimpleNamespace(id=bk.id), None, TZ, None, {1}, T))
    return cb.answers


def refund_flag(calls):
    return [c[2]["refund"] for c in calls.called("cancel_booking")]


def test_early_cancel_refunds_the_deposit(calls):
    assert cancel(calls, booking()) == [T.CANCELLED_REFUNDED]
    assert refund_flag(calls) == [True]
    assert len(calls.notified) == 1  # the master hears about the cancellation
    assert not calls.called("alert_refund_failed")


def test_failed_refund_is_reported_as_in_progress(calls):
    # Not "less than 24 h before the visit", which is what the client used to see
    assert cancel(calls, booking(), refunded=False) == [T.CANCELLED_REFUND_PENDING]
    assert refund_flag(calls) == [True]
    assert len(calls.called("alert_refund_failed")) == 1


def test_late_cancel_keeps_the_deposit(calls):
    assert cancel(calls, booking(hours_ahead=2)) == [T.CANCELLED_NO_REFUND]
    assert refund_flag(calls) == [False]
    assert not calls.called("refund")


def test_releasing_a_hold_bothers_nobody(calls):
    answers = cancel(calls, booking(BookingStatus.PENDING, charge=None, created_at=NOW))
    assert answers == [T.CANCELLED]
    assert calls.notified == []
    assert scheduling.cooldown_left(CLIENT_ID, NOW) is None  # free to pick another time


def test_quick_cancel_of_a_fresh_booking_starts_the_cooldown(calls):
    cancel(calls, booking(charge=None, created_at=NOW - timedelta(minutes=5)))
    assert scheduling.cooldown_left(CLIENT_ID, NOW) == scheduling.REBOOK_COOLDOWN


def test_cancel_that_lost_the_race_changes_nothing(calls):
    assert cancel(calls, booking(), won=False) == [T.CANT_CANCEL]
    assert not calls.called("refund")
    assert calls.notified == []


def test_someone_elses_booking_cant_be_cancelled(calls):
    assert cancel(calls, booking(), user_id=99) == [T.CANT_CANCEL]
    assert not calls.called("cancel_booking")


@pytest.mark.parametrize(
    ("bk", "note"),
    [
        (booking(), T.CANCEL_ASK_REFUND.format(stars=50)),
        (booking(hours_ahead=2), T.CANCEL_ASK_NO_REFUND.format(stars=50)),
        (booking(charge=None), ""),
        (booking(BookingStatus.PENDING, charge=None), ""),
    ],
)
def test_cancel_question_says_what_happens_to_the_deposit(bk, note):
    assert client.deposit_note(T, bk, NOW) == note


def test_double_tap_on_confirm_gets_a_silent_answer():
    assert client.refusal_text(T, scheduling.AlreadyBookedError()) is None
    assert client.refusal_text(T, scheduling.HoldExistsError()) == T.HOLD_EXISTS


# --- Where the handlers answer ---


def chat_message(chat_type, text="hi", user_id=1):
    return SimpleNamespace(
        chat=SimpleNamespace(type=chat_type), text=text, from_user=SimpleNamespace(id=user_id)
    )


@pytest.mark.parametrize(("chat_type", "answered"), [("private", True), ("supergroup", False)])
def test_booking_and_panel_work_in_private_chats_only(chat_type, answered):
    message = chat_message(chat_type)
    callback = SimpleNamespace(message=message, from_user=message.from_user)
    for observer, event in (
        (client.router.message, message),
        (client.router.callback_query, callback),
        (admin.router.message, message),
        (admin.router.callback_query, callback),
    ):
        passed, _ = asyncio.run(observer.check_root_filters(event, admin_ids={1}))
        assert passed is answered


def test_fallback_ignores_service_messages():
    fallback = next(h for h in client.router.message.handlers if h.callback is client.fallback)
    assert asyncio.run(fallback.check(chat_message("private", text="hello")))[0]
    # e.g. the notice Telegram sends after a refund
    assert not asyncio.run(fallback.check(chat_message("private", text=None)))[0]


# --- /paysupport ---


@pytest.mark.parametrize(
    ("contact", "expected"),
    [
        ("", T.PAYSUPPORT),
        ("@shop<b>", T.PAYSUPPORT + T.PAYSUPPORT_CONTACT.format(contact="@shop&lt;b&gt;")),
    ],
)
def test_paysupport_contact(contact, expected):
    message = FakeMessage()
    asyncio.run(pay_handlers.paysupport(message, T, contact))
    assert message.sent == [expected]

"""SlotBook master panel: the paginated booking list and the input steps."""

import asyncio
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from zoneinfo import ZoneInfo

import pytest
from aiogram.dispatcher.event.bases import SkipHandler

from slotbook import keyboards as kb
from slotbook.handlers import admin
from slotbook.models import USER_NAME_LEN, BookingStatus
from slotbook.texts import TEXTS

TZ = ZoneInfo("Europe/Moscow")
START = datetime(2026, 11, 2, 7, tzinfo=UTC)
TELEGRAM_TEXT_LIMIT = 4096


def week_of_bookings(count: int) -> list[SimpleNamespace]:
    """`count` bookings over a week with the longest names, every other one an unpaid hold."""
    return [
        SimpleNamespace(
            id=i + 1,
            user_id=10**12 + i,
            user_name=("<Name & Co>" * 12)[:USER_NAME_LEN],
            starts_at=START + timedelta(days=i % 7, minutes=30 * (i // 7)),
            ends_at=START + timedelta(days=i % 7, minutes=30 * (i // 7) + 30),
            status=BookingStatus.PENDING if i % 2 else BookingStatus.ACTIVE,
            service=SimpleNamespace(name="S" * 64),
        )
        for i in range(count)
    ]


def cancel_ids(markup) -> list[int]:
    ids = []
    for row in markup.inline_keyboard:
        for button in row:
            if button.callback_data.startswith("a:cancel:"):
                ids.append(kb.Admin.unpack(button.callback_data).id)
    return ids


def page_arrows(markup) -> list[int]:
    return [
        kb.AdminPage.unpack(b.callback_data).page
        for row in markup.inline_keyboard
        for b in row
        if b.callback_data.startswith("ap:")
    ]


def test_every_booking_of_a_busy_week_gets_a_cancel_button():
    items = week_of_bookings(65)
    seen = []
    pages = admin.paginate(items, 0)[2]
    for page in range(pages):
        chunk, _, _ = admin.paginate(items, page)
        assert len(chunk) <= admin.PAGE_SIZE
        seen += cancel_ids(kb.admin_bookings(TEXTS["en"], chunk, TZ, 7, page, pages))
    assert seen == [b.id for b in items]


@pytest.mark.parametrize("lang", list(TEXTS))
def test_a_full_page_fits_one_message(lang):
    t = TEXTS[lang]
    chunk, page, pages = admin.paginate(week_of_bookings(65), 1)
    text = admin.bookings_text(t, chunk, TZ, page, pages)
    # The raw HTML is longer than what Telegram counts, so this is a safe upper bound
    assert len(text) < TELEGRAM_TEXT_LIMIT
    assert "&lt;Name &amp; Co&gt;" in text  # names are escaped...
    assert "<Name" not in text
    assert t.HOLD_MARK in text  # ...and unpaid holds are marked


def test_long_names_are_cut_in_list_and_buttons():
    chunk, page, pages = admin.paginate(week_of_bookings(1), 0)
    full_name = chunk[0].user_name
    assert full_name not in admin.bookings_text(TEXTS["en"], chunk, TZ, page, pages)
    button = kb.admin_bookings(TEXTS["en"], chunk, TZ, 7, page, pages).inline_keyboard[0][0]
    assert full_name not in button.text
    assert button.text.endswith("…")


@pytest.mark.parametrize(("asked", "shown", "arrows"), [(0, 0, [1]), (1, 1, [0, 2]), (99, 3, [2])])
def test_pages_are_clamped_and_linked(asked, shown, arrows):
    items = week_of_bookings(65)  # 4 pages
    chunk, page, pages = admin.paginate(items, asked)
    assert (page, pages) == (shown, 4)
    assert page_arrows(kb.admin_bookings(TEXTS["en"], chunk, TZ, 7, page, pages)) == arrows


def test_single_page_has_no_counter_or_arrows():
    chunk, page, pages = admin.paginate(week_of_bookings(3), 0)
    assert pages == 1
    assert not admin.bookings_text(TEXTS["en"], chunk, TZ, page, pages).endswith("1/1")
    assert page_arrows(kb.admin_bookings(TEXTS["en"], chunk, TZ, 7, page, pages)) == []


# --- Input steps ---


class FakeState:
    def __init__(self):
        self.cleared = False
        self.state = None

    async def clear(self):
        self.cleared = True

    async def set_state(self, state):
        self.state = state

    async def update_data(self, **data):
        pass


def test_command_during_input_ends_the_step_and_runs():
    state = FakeState()
    with pytest.raises(SkipHandler):  # handed on to the command's own handler
        asyncio.run(admin.command_during_input(SimpleNamespace(text="/start"), state))
    assert state.cleared


@pytest.mark.parametrize("text", ["/start", "/paysupport@slotbook_bot"])
def test_input_steps_dont_take_commands(text):
    assert not admin.ANSWER.resolve(SimpleNamespace(text=text))
    assert admin.ANSWER.resolve(SimpleNamespace(text="Beard trim"))


def test_forged_weekday_is_ignored():
    answers, state = [], FakeState()

    async def answer(text=None, **kw):
        answers.append(text)

    cb = SimpleNamespace(answer=answer, message=None)
    asyncio.run(admin.hours_edit_start(cb, kb.Admin(action="hours_edit", id=7), state, TEXTS["en"]))
    assert answers == [None]
    assert state.state is None

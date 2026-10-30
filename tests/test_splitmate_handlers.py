"""SplitMates handlers, run with stand-ins for Telegram and the database."""

import asyncio
import html
from types import SimpleNamespace

import pytest
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command
from aiogram.methods import EditMessageText
from aiogram.types import CallbackQuery, User

from splitmate import keyboards as kb
from splitmate import repo
from splitmate.handlers import group
from splitmate.handlers.inline import expense_message
from splitmate.money import MAX_AMOUNT, parse_amount
from splitmate.texts import TEXTS

t = TEXTS["en"]
CHAT = -100
PAYER, BOB, CAROL = 1, 2, 3
# The payer tapped Carol in the "who pays what" editor (message 50); the question is message 60
QUESTION = {"expense": 7, "user": CAROL, "editor": 50, "prompts": [60]}


class FakeState:
    def __init__(self, data=None):
        self.data = dict(data or {})

    async def get_data(self):
        return dict(self.data)

    async def set_data(self, data):
        self.data = dict(data)

    async def update_data(self, **kwargs):
        self.data.update(kwargs)

    async def set_state(self, state):
        pass

    async def clear(self):
        self.data = {}


class FakeBot:
    id = 42

    def __init__(self, edit_error=None):
        self.deleted = []
        self.edit_error = edit_error

    async def delete_message(self, chat_id, message_id):
        self.deleted.append(message_id)

    async def edit_message_text(self, text, **kwargs):
        if self.edit_error:
            raise self.edit_error


class FakeMessage:
    def __init__(self, text="", reply_to=None, user_id=PAYER, **fields):
        self.text = text
        self.message_id = 100
        self.chat = SimpleNamespace(id=CHAT, title="Trip", type="supergroup")
        self.from_user = SimpleNamespace(id=user_id, full_name="Ann", first_name="Ann")
        self.reply_to_message = SimpleNamespace(message_id=reply_to) if reply_to else None
        self.sender_chat = self.forward_origin = self.via_bot = None
        self.__dict__.update(fields)
        self.sent = []

    async def reply(self, text, **kwargs):
        self.sent.append(text)
        return SimpleNamespace(message_id=200 + len(self.sent))

    async def answer(self, text, **kwargs):
        self.sent.append(text)
        return SimpleNamespace(message_id=300 + len(self.sent))

    async def edit_text(self, text, **kwargs):
        self.sent.append(text)


class FakeCallback:
    def __init__(self, user_id=PAYER):
        self.from_user = SimpleNamespace(id=user_id, full_name="Ann", first_name="Ann")
        self.message = FakeMessage()
        self.answers = []

    async def answer(self, text=None, show_alert=False):
        self.answers.append((text, show_alert))


def expense(expense_id=7, payer=PAYER, people=(PAYER, BOB, CAROL), deleted=False):
    shares = [SimpleNamespace(user_id=uid, amount=100, fixed=False) for uid in people]
    return SimpleNamespace(
        id=expense_id,
        chat_id=CHAT,
        payer_id=payer,
        amount=100 * len(people),
        description="",
        is_deleted=deleted,
        shares=shares,
    )


async def must_not_be_called(*args, **kwargs):
    raise AssertionError("must not be called")


async def nothing(*args, **kwargs):
    return None


async def a_chat(*args, **kwargs):
    return SimpleNamespace(id=CHAT, currency="$")


# --- Answers to "how much for X?" ---


def test_only_a_reply_to_the_current_question_is_an_answer(monkeypatch):
    # The payer tapped Bob, then Carol, then answered Bob's (older) question
    monkeypatch.setattr(repo, "get_expense", must_not_be_called)
    state, message = FakeState(QUESTION), FakeMessage("150", reply_to=59)
    asyncio.run(group.share_entered(message, None, state, FakeBot(), t))
    assert state.data == QUESTION and message.sent == []


def test_answer_about_a_deleted_expense_is_dropped_before_parsing(monkeypatch):
    async def deleted(session, expense_id, lock=False):
        return expense(deleted=True)

    monkeypatch.setattr(repo, "get_expense", deleted)
    state, bot = FakeState({**QUESTION, "cleanup": [61]}), FakeBot()
    message = FakeMessage("no idea", reply_to=60)
    asyncio.run(group.share_entered(message, None, state, bot, t))
    assert message.sent == []  # no "couldn't read the amount" for a deleted expense
    assert state.data == {} and bot.deleted == [60, 61]


def test_same_amount_again_still_tidies_up(monkeypatch):
    locks = []

    async def get_expense(session, expense_id, lock=False):
        locks.append(lock)
        return expense()

    async def view(*args):
        return "editor", None

    monkeypatch.setattr(repo, "get_expense", get_expense)
    monkeypatch.setattr(repo, "set_share", nothing)
    monkeypatch.setattr(group, "amounts_view", view)
    not_modified = TelegramBadRequest(EditMessageText(text="x"), "message is not modified")
    state = FakeState({**QUESTION, "prompts": [60, 62], "cleanup": [61]})
    bot = FakeBot(edit_error=not_modified)
    message = FakeMessage("1,50", reply_to=62)  # a reply to the hint after a wrong answer
    asyncio.run(group.share_entered(message, None, state, bot, t))
    assert locks == [True]
    assert state.data == {} and bot.deleted == [60, 62, 61, message.message_id]


def test_commands_are_never_taken_for_an_answer():
    handlers = group.router.message.handlers
    answer = next(i for i, h in enumerate(handlers) if h.callback is group.share_entered)
    commands = [
        i for i, h in enumerate(handlers) if any(isinstance(f.callback, Command) for f in h.filters)
    ]
    assert max(commands) < answer  # /balance is handled before the answer handler sees it

    def matches(message):
        state = group.EnterShare.amount.state
        return asyncio.run(handlers[answer].check(message, raw_state=state))[0]

    assert matches(FakeMessage("150", reply_to=60))
    assert not matches(FakeMessage("/balance", reply_to=60))
    assert not matches(FakeMessage("150"))  # not a reply to the bot's question


def test_new_question_replaces_the_old_one(monkeypatch):
    async def load(*args, **kwargs):
        return expense()

    async def names(*args):
        return {BOB: "Bob", CAROL: "Carol"}

    monkeypatch.setattr(group, "load_editable_expense", load)
    monkeypatch.setattr(repo, "ensure_chat", a_chat)
    monkeypatch.setattr(repo, "names", names)
    state, bot, cb = FakeState(QUESTION), FakeBot(), FakeCallback()
    asyncio.run(group.pick_share(cb, kb.PickShare(expense=7, user=BOB), None, state, bot, t))
    assert bot.deleted == [60]  # the question about Carol is gone
    assert state.data["user"] == BOB and state.data["prompts"] == [301]


@pytest.mark.parametrize("action", ["done", "delete"])
@pytest.mark.parametrize(("pressed", "forgotten"), [(7, True), (8, False)])
def test_done_and_delete_drop_the_question_about_that_expense(
    monkeypatch, action, pressed, forgotten
):
    async def load(cb, session, bot, t, expense_id, lock=False):
        return expense(expense_id)

    async def text(*args):
        return "expense"

    monkeypatch.setattr(group, "load_editable_expense", load)
    monkeypatch.setattr(group, "expense_text", text)
    monkeypatch.setattr(repo, "ensure_chat", a_chat)
    monkeypatch.setattr(repo, "delete_expense", nothing)
    handler = group.people_done if action == "done" else group.delete_expense
    state, bot = FakeState(QUESTION), FakeBot()
    callback_data = kb.ExpenseAction(action=action, id=pressed)
    asyncio.run(handler(FakeCallback(), callback_data, None, state, bot, t))
    assert (state.data == {}) is forgotten
    assert bot.deleted == ([60] if forgotten else [])


# --- Participants ---


@pytest.mark.parametrize(("payer", "split"), [(PAYER, {PAYER, CAROL}), (BOB, {PAYER, BOB, CAROL})])
def test_new_expenses_skip_those_who_left_except_the_payer(monkeypatch, payer, split):
    people = [
        SimpleNamespace(user_id=PAYER, active=True),
        SimpleNamespace(user_id=BOB, active=False),  # sent /leave
        SimpleNamespace(user_id=CAROL, active=True),
    ]
    recorded = []

    async def members(*args):
        return people

    async def add_expense(session, chat_id, payer_id, amount, description, ids):
        recorded.append(set(ids))
        return expense()

    async def text(*args):
        return "expense"

    monkeypatch.setattr(repo, "ensure_chat", a_chat)
    monkeypatch.setattr(repo, "ensure_member", nothing)
    monkeypatch.setattr(repo, "members", members)
    monkeypatch.setattr(repo, "add_expense", add_expense)
    monkeypatch.setattr(group, "expense_text", text)
    message = FakeMessage("/add 300", user_id=payer)
    asyncio.run(group.record_expense(message, None, t, message.from_user, 30000, ""))
    assert recorded == [split]


@pytest.mark.parametrize(("who", "left"), [(BOB, [BOB]), (FakeBot.id, [])])
def test_leaving_the_group_works_like_leave(monkeypatch, who, left):
    calls = []

    async def leave(session, chat_id, user_id):
        calls.append(user_id)

    monkeypatch.setattr(repo, "leave", leave)
    message = FakeMessage(left_chat_member=SimpleNamespace(id=who))
    asyncio.run(group.member_left(message, None, FakeBot()))
    assert calls == left  # the bot itself being removed changes nothing


@pytest.mark.parametrize(
    "fields", [{"migrate_to_chat_id": -200}, {"migrate_from_chat_id": CHAT}], ids=["old", "new"]
)
def test_upgrade_to_supergroup_moves_from_old_to_new_id(monkeypatch, fields):
    moves = []

    async def move_chat(session, old_id, new_id):
        moves.append((old_id, new_id))

    monkeypatch.setattr(repo, "move_chat", move_chat)
    message = FakeMessage(migrate_to_chat_id=None, migrate_from_chat_id=None)
    message.__dict__.update(fields)
    if "migrate_from_chat_id" in fields:
        message.chat.id = -200  # the report in the new supergroup
    asyncio.run(group.group_upgraded(message, None))
    assert moves == [(CHAT, -200)]


# --- Expenses ---


def test_count_me_in_joins_first_then_changes_the_locked_expense(monkeypatch):
    # C and D pressing at once must not both split the old shares (4 shares, 13.33 of 10.00)
    calls = []

    async def ensure_member(session, chat_id, user, rejoin=False):
        calls.append("join")

    async def get_expense(session, expense_id, lock=False):
        calls.append(f"load, lock={lock}")
        return expense(people=(PAYER, BOB))

    async def set_participants(session, expense, ids):
        calls.append(f"split between {sorted(ids)}")

    async def text(*args):
        return "expense"

    monkeypatch.setattr(repo, "ensure_member", ensure_member)
    monkeypatch.setattr(repo, "get_expense", get_expense)
    monkeypatch.setattr(repo, "set_participants", set_participants)
    monkeypatch.setattr(repo, "ensure_chat", a_chat)
    monkeypatch.setattr(group, "expense_text", text)
    asyncio.run(group.me_too(FakeCallback(user_id=CAROL), kb.MeToo(expense=7), None, t))
    # Joining commits, which would release the lock: it has to come first
    assert calls == ["join", "load, lock=True", f"split between {[PAYER, BOB, CAROL]}"]


@pytest.mark.parametrize(("admin", "allowed"), [(True, True), (False, False)])
def test_chat_admins_may_change_anyones_expense(monkeypatch, admin, allowed):
    async def get_expense(session, expense_id, lock=False):
        return expense(payer=PAYER)

    async def is_admin(bot, chat_id, user_id):
        return admin

    monkeypatch.setattr(repo, "get_expense", get_expense)
    monkeypatch.setattr(group, "is_admin", is_admin)
    cb = FakeCallback(user_id=BOB)
    found = asyncio.run(group.load_editable_expense(cb, None, FakeBot(), t, 7))
    assert (found is not None) is allowed
    assert cb.answers == ([] if allowed else [(t.ONLY_PAYER, True)])


def test_posts_on_behalf_of_a_chat_are_turned_away(monkeypatch):
    for name in ("ensure_chat", "ensure_member", "leave"):
        monkeypatch.setattr(repo, name, must_not_be_called)
    the_group = SimpleNamespace(id=CHAT, type="supergroup")  # an anonymous admin
    add, join, leave = (FakeMessage(sender_chat=the_group) for _ in range(3))
    asyncio.run(group.record_expense(add, None, t, add.from_user, 10000, "taxi"))
    asyncio.run(group.join_cmd(join, None, t))
    asyncio.run(group.leave_cmd(leave, None, t))
    assert add.sent == join.sent == leave.sent == [t.POST_AS_YOURSELF]


def test_forwarded_inline_expense_is_not_recorded_again(monkeypatch):
    recorded = []

    async def record_expense(message, session, t, payer, amount, description):
        recorded.append((amount, description))

    monkeypatch.setattr(group, "record_expense", record_expense)
    bot = FakeBot()
    sent = FakeMessage(f"{group.INLINE_PREFIX}300 pizza", via_bot=SimpleNamespace(id=bot.id))
    forward = FakeMessage(sent.text, via_bot=sent.via_bot, forward_origin=SimpleNamespace())
    asyncio.run(group.inline_expense(sent, None, bot, t))
    asyncio.run(group.inline_expense(forward, None, bot, t))
    assert recorded == [(30000, "pizza")]


@pytest.mark.parametrize(
    "description", ["pizza <3", '<a href="https://evil.example">Pay here</a>', "Tom & Jerry"]
)
def test_inline_message_is_plain_text_in_html(description):
    text = expense_message(30000, description)
    assert "<" not in text and ">" not in text
    # The group gets the text with entities decoded, and the bot parses it back
    shown = html.unescape(text)
    assert parse_amount(shown.removeprefix(group.INLINE_PREFIX)) == (30000, description)


# --- Settling up ---


def test_settle_records_only_the_amount_on_the_button(monkeypatch):
    recorded = []

    async def record_settlement(session, chat_id, debtor, creditor, amount):
        recorded.append((debtor, creditor, amount))
        return False  # the debt has grown since the button was shown

    monkeypatch.setattr(repo, "ensure_chat", a_chat)
    monkeypatch.setattr(repo, "record_settlement", record_settlement)
    cb = FakeCallback(user_id=PAYER)
    button = kb.Settle(debtor=BOB, creditor=PAYER, amount=5000)
    asyncio.run(group.settle(cb, button, None, t))
    assert recorded == [(BOB, PAYER, 5000)]
    assert cb.answers == [(t.SETTLE_STALE, True)]


def test_settle_button_carries_the_amount_and_fits_telegram_limit():
    markup = kb.settle([(BOB, PAYER, 5000)], {BOB: "Bob", PAYER: "Ann"}, "$")
    assert kb.Settle.unpack(markup.inline_keyboard[0][0].callback_data).amount == 5000
    # User ids have up to 52 significant bits; callback data is limited to 64 bytes
    biggest = kb.Settle(debtor=2**52, creditor=2**52, amount=MAX_AMOUNT).pack()
    assert len(biggest.encode()) <= 64


def test_old_settle_buttons_without_amount_are_answered():
    handlers = group.router.callback_query.handlers
    new = next(h for h in handlers if h.callback is group.settle)
    old = next(h for h in handlers if h.callback is group.old_settle_button)
    assert handlers.index(new) < handlers.index(old)

    def matches(handler, data):
        user = User(id=PAYER, is_bot=False, first_name="Ann")
        query = CallbackQuery(id="1", from_user=user, chat_instance="1", data=data)
        return asyncio.run(handler.check(query))[0]

    button = kb.Settle(debtor=BOB, creditor=PAYER, amount=5000).pack()
    assert matches(new, button)
    assert not matches(new, f"st:{BOB}:{PAYER}") and matches(old, f"st:{BOB}:{PAYER}")
    cb = FakeCallback()
    asyncio.run(group.old_settle_button(cb, t))
    assert cb.answers == [(t.SETTLE_STALE, True)]

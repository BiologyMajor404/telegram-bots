"""ChatGuard routing and group handlers: nothing gets past the guard, admin checks, Restore,
and a group becoming a supergroup."""

import asyncio
from datetime import UTC, date, datetime
from types import SimpleNamespace

import pytest
from aiogram.dispatcher.event.bases import UNHANDLED
from aiogram.types import Chat as TgChat
from aiogram.types import ChatMemberAdministrator, Message, PhotoSize, User

from chatguard import __main__ as app
from chatguard import keyboards as kb
from chatguard import repo
from chatguard.config import Plans
from chatguard.handlers import group, guard
from chatguard.models import Action, Chat, Incident
from chatguard.texts import TEXTS
from shared.i18n import CHOOSE_LANGUAGE

EN = TEXTS["en"]
GROUP = -1001000000001
CHANNEL = -1002000000002
SPAM_COMMAND = "/paysupport Earn 500$ a day t.me/+AbCd"


def run(coro):
    return asyncio.run(coro)


class RecordingBot:
    """Takes the API calls a bound aiogram object makes (e.g. message.answer)."""

    def __init__(self):
        self.methods = []

    async def __call__(self, method, request_timeout=None):
        self.methods.append(method)


def tg_message(chat_type: str, **fields) -> Message:
    chat_id = 7 if chat_type == "private" else GROUP
    return Message(
        message_id=1,
        date=datetime.now(UTC),
        chat=TgChat(id=chat_id, type=chat_type, title=None if chat_type == "private" else "G"),
        from_user=User(id=7, is_bot=False, first_name="Anna"),
        **fields,
    )


async def dispatch(message: Message, bot) -> str | None:
    """Offer a message to the routers in order, as the dispatcher does; the name of the
    router that took it, None if nobody did."""
    data = {
        "bot": bot,
        "session": None,
        "t": EN,
        "classifier": None,
        "plans": Plans(50, 300, 250, 1500),
        "support_contact": "",
    }
    for router in app.routers():
        if await router.propagate_event("message", message, **data) is not UNHANDLED:
            return router.name
    return None


# --- Routing ---


def test_guard_is_the_first_router():
    assert app.routers()[0] is guard.router


@pytest.mark.parametrize(
    "fields",
    [
        {"text": SPAM_COMMAND},
        {
            "caption": SPAM_COMMAND,
            "photo": [PhotoSize(file_id="f", file_unique_id="u", width=1, height=1)],
        },
    ],
)
def test_group_paysupport_with_spam_reaches_the_guard(monkeypatch, fields):
    seen = []

    async def spam_guard(message, *args, **kwargs):
        seen.append(message.text or message.caption)
        return True  # spam: removed

    monkeypatch.setattr(guard, "guard", spam_guard)
    assert run(dispatch(tg_message("supergroup", **fields), RecordingBot())) == "guard"
    assert seen == [SPAM_COMMAND]


def test_paysupport_is_answered_in_private_chats_only(monkeypatch):
    async def clean(message, *args, **kwargs):
        return False

    monkeypatch.setattr(guard, "guard", clean)
    bot = RecordingBot()
    assert run(dispatch(tg_message("supergroup", text="/paysupport").as_(bot), bot)) is None
    assert run(dispatch(tg_message("private", text="/paysupport").as_(bot), bot)) == "payments"
    assert [m.text for m in bot.methods] == [EN.PAYSUPPORT]


def test_migrate_message_reaches_the_migration_through_the_guard(monkeypatch):
    moves = []

    async def migrate_chat(session, old_id, new_id):
        moves.append((old_id, new_id))

    monkeypatch.setattr(repo, "migrate_chat", migrate_chat)
    old_group = tg_message("group", migrate_to_chat_id=GROUP - 1)
    assert run(dispatch(old_group, RecordingBot())) == "group"
    supergroup = tg_message("supergroup", migrate_from_chat_id=-5)
    assert run(dispatch(supergroup, RecordingBot())) == "group"
    assert moves == [(GROUP, GROUP - 1), (-5, GROUP)]


# --- Admin commands ---


class FakeGroupMessage:
    def __init__(self, sender_chat):
        self.chat = SimpleNamespace(id=GROUP, title="G", type="supergroup")
        self.from_user = SimpleNamespace(id=1087968824, full_name="Group")  # a placeholder bot
        self.sender_chat = sender_chat
        self.answered, self.replied = [], []

    async def answer(self, text, **kwargs):
        self.answered.append(text)

    async def reply(self, text, **kwargs):
        self.replied.append(text)


def test_anonymous_admin_can_use_admin_commands():
    message = FakeGroupMessage(sender_chat=SimpleNamespace(id=GROUP))
    run(group.language_cmd(message, RecordingBot(), EN))
    assert message.answered == [CHOOSE_LANGUAGE]


def test_posting_as_a_channel_is_not_being_an_admin():
    message = FakeGroupMessage(sender_chat=SimpleNamespace(id=CHANNEL))
    run(group.language_cmd(message, RecordingBot(), EN))
    assert message.replied == [EN.ONLY_ADMINS]


# --- Restore ---


class RestoreBot:
    def __init__(self, can_restrict: bool):
        self.member = ChatMemberAdministrator.model_construct(
            status="administrator", can_delete_messages=True, can_restrict_members=can_restrict
        )
        self.calls = []

    async def get_chat_member(self, chat_id, user_id):
        return self.member

    async def unban_chat_sender_chat(self, chat_id, sender_chat_id):
        self.calls.append(("unban_channel", sender_chat_id))

    async def unban_chat_member(self, chat_id, user_id, only_if_banned):
        self.calls.append(("unban", user_id))


class FakeCallback:
    def __init__(self):
        self.from_user = SimpleNamespace(id=9, full_name="Admin")
        self.message = SimpleNamespace(chat=SimpleNamespace(id=GROUP), edit_text=self.edit_text)
        self.answers, self.edited = [], []

    async def answer(self, text=None, show_alert=False):
        self.answers.append((text, show_alert))

    async def edit_text(self, text, **kwargs):
        self.edited.append(text)


@pytest.fixture
def incident(monkeypatch):
    found = Incident(
        id=1,
        chat_id=GROUP,
        user_id=CHANNEL,
        user_name="Crypto t.me/+abc",
        text="Earn now",
        action=Action.BAN,
        restored=False,
    )

    async def get_incident(session, incident_id):
        return found

    async def restore(session, incident):
        incident.restored = True

    monkeypatch.setattr(repo, "get_incident", get_incident)
    monkeypatch.setattr(repo, "restore", restore)
    return found


def test_restore_needs_the_right_to_ban_users(incident):
    cb, bot = FakeCallback(), RestoreBot(can_restrict=False)
    run(group.restore(cb, kb.Restore(incident=1), None, bot, EN))
    assert cb.answers == [(EN.RESTORE_NEEDS_RIGHT, True)]
    assert bot.calls == [] and not incident.restored


def test_restore_unbans_a_channel(incident):
    cb, bot = FakeCallback(), RestoreBot(can_restrict=True)
    run(group.restore(cb, kb.Restore(incident=1), None, bot, EN))
    assert bot.calls == [("unban_channel", CHANNEL)] and incident.restored
    assert "Crypto" in cb.edited[0] and "t.me" not in cb.edited[0]


# --- A group becoming a supergroup ---


def test_supergroup_takes_over_the_groups_settings_and_plan():
    today = date(2026, 10, 30)
    until = datetime(2026, 11, 20, tzinfo=UTC)
    old = Chat(
        id=-5,
        lang="uk",
        enabled=False,
        action=Action.BAN,
        checked=10,
        caught=2,
        ai_day=today,
        ai_checks=3,
        pro_until=until,
        pro_owner_id=42,
        pro_charge_id="charge",
    )
    # The defaults the first update from the supergroup created
    new = Chat(id=GROUP, lang="en", enabled=True, action=Action.MUTE, checked=1, caught=0)
    new.ai_day, new.ai_checks = today, 1
    repo.take_over(new, old)
    assert (new.lang, new.enabled, new.action) == ("uk", False, Action.BAN)
    assert (new.checked, new.caught, new.ai_checks) == (11, 2, 4)
    assert (new.pro_until, new.pro_owner_id, new.pro_charge_id) == (until, 42, "charge")
    assert new.migrated_from == -5

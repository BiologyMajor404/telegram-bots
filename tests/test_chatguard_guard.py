"""ChatGuard spam guard: who gets checked, what is done to spam and reported, the AI budget.
Telegram and the database are replaced by fakes."""

import asyncio
from datetime import date
from types import SimpleNamespace

import pytest
from aiogram.exceptions import TelegramBadRequest
from aiogram.methods import DeleteMessage
from aiogram.types import ChatMemberAdministrator, ChatMemberMember, ChatMemberOwner

from chatguard import repo, rights
from chatguard.ai import AiVerdict
from chatguard.config import Plans
from chatguard.handlers import guard
from chatguard.models import Action, Chat, Member
from chatguard.rights import NO_RIGHTS, Rights
from chatguard.texts import TEXTS

EN = TEXTS["en"]
GROUP = -1001000000001
CHANNEL = -1002000000002
SPAM = "Заработок крипта инвест пиши в лс t.me/+abc"  # spam by the rules alone
DOUBTFUL = "Смотрите https://site.xyz"  # the AI decides
PLANS = Plans(free_limit=50, pro_limit=300, pro_price_stars=250, global_limit=1500)
REFUSED = DeleteMessage(chat_id=GROUP, message_id=1)


def run(coro):
    return asyncio.run(coro)


def admin(*, delete: bool = True, restrict: bool = True) -> ChatMemberAdministrator:
    return ChatMemberAdministrator.model_construct(
        status="administrator", can_delete_messages=delete, can_restrict_members=restrict
    )


class FakeBot:
    """Records what the guard asks Telegram to do; the calls named in `refuse` fail."""

    id = 42

    def __init__(self, me=None, refuse=(), linked=None):
        self.me = me or admin()
        self.refuse = set(refuse)
        self.linked = linked
        self.calls = []
        self.sent = []

    async def _do(self, name, target):
        self.calls.append((name, target))
        if name in self.refuse:
            raise TelegramBadRequest(REFUSED, f"{name} refused")

    async def get_chat_member(self, chat_id, user_id):
        return self.me if user_id == self.id else ChatMemberMember.model_construct()

    async def get_chat(self, chat_id):
        return SimpleNamespace(linked_chat_id=self.linked)

    async def restrict_chat_member(self, chat_id, user_id, permissions):
        await self._do("mute", user_id)

    async def ban_chat_member(self, chat_id, user_id):
        await self._do("ban", user_id)

    async def ban_chat_sender_chat(self, chat_id, sender_chat_id):
        await self._do("ban_channel", sender_chat_id)

    async def send_message(self, chat_id, text, **kwargs):
        self.sent.append(text)


class FakeMessage:
    def __init__(self, text, *, sender_chat=None, automatic=None, delete_error=None):
        self.text, self.caption = text, None
        self.chat = SimpleNamespace(id=GROUP, title="Group", type="supergroup")
        self.from_user = SimpleNamespace(id=7, is_bot=False, full_name="Anna t.me/+spam")
        self.sender_chat = sender_chat
        self.is_automatic_forward = automatic
        self.entities = self.caption_entities = self.forward_origin = self.reply_markup = None
        self.delete_error = delete_error
        self.deleted = False

    async def delete(self):
        if self.delete_error:
            raise TelegramBadRequest(REFUSED, self.delete_error)
        self.deleted = True


class FakeSession:
    async def commit(self):
        pass


class FakeClassifier:
    def __init__(self, verdict):
        self.verdict = verdict
        self.calls = 0

    async def classify(self, text, lang, hints, allow_opus=True):
        self.calls += 1
        return self.verdict


def channel(title="Crypto news t.me/+abc", chat_id=CHANNEL):
    return SimpleNamespace(id=chat_id, title=title)


@pytest.fixture
def db(monkeypatch):
    """The guard's database calls, kept in memory; the module caches start empty."""
    state = SimpleNamespace(
        chat=Chat(id=GROUP, title="Group", lang="en", enabled=True, action=Action.MUTE),
        member=Member(chat_id=GROUP, user_id=7, clean_messages=0, trusted=False),
        spammers=[],
        incidents=[],
        global_limits=[],
        stats=[],
    )

    async def ensure_chat(session, chat_id, title, lang="ru"):
        return state.chat

    async def get_member(session, chat_id, user_id):
        return state.member

    async def is_known_spammer(session, user_id):
        return False

    async def reserve_ai_check(session, chat_id, today, limit):
        return True

    async def reserve_global_ai_check(session, today, limit):
        state.global_limits.append(limit)
        return True

    async def count_clean(session, chat_id, user_id):
        state.member.clean_messages += 1

    async def bump_stats(session, chat_id, checked=0, caught=0):
        state.stats.append((checked, caught))

    async def record_spammer(session, user_id, chat_id, now):
        state.spammers.append((user_id, chat_id))

    async def add_incident(session, **fields):
        state.incidents.append(fields)
        return SimpleNamespace(id=len(state.incidents), **fields)

    for fake in (
        ensure_chat,
        get_member,
        is_known_spammer,
        reserve_ai_check,
        reserve_global_ai_check,
        count_clean,
        bump_stats,
        record_spammer,
        add_incident,
    ):
        monkeypatch.setattr(repo, fake.__name__, fake)

    async def not_admin(bot, chat_id, user_id):
        return False

    monkeypatch.setattr(guard, "is_admin", not_admin)
    for cache in ("_user_ai_checks", "_no_rights_noticed", "_linked_channels"):
        monkeypatch.setattr(guard, cache, {})
    monkeypatch.setattr(rights, "_bot_rights", {})
    return state


def check_message(message, bot, classifier=None, *, edited=False):
    return run(guard.guard(message, FakeSession(), bot, EN, classifier, PLANS, edited=edited))


# --- Who is checked ---


def test_anonymous_admins_channel_autoforwards_and_bots_are_not_checked():
    anonymous_admin = FakeMessage("hi", sender_chat=SimpleNamespace(id=GROUP, title="Group"))
    autoforward = FakeMessage("post", sender_chat=channel(), automatic=True)
    from_bot = FakeMessage("hi")
    from_bot.from_user.is_bot = True
    for message in (anonymous_admin, autoforward, from_bot):
        assert guard.sender_of(message) is None


def test_people_and_other_channels_are_checked_as_themselves():
    assert guard.sender_of(FakeMessage("hi")) == guard.Sender(7, "Anna t.me/+spam")
    posted_as_channel = FakeMessage("hi", sender_chat=channel("Free money"))
    assert guard.sender_of(posted_as_channel) == guard.Sender(CHANNEL, "Free money")


def test_spam_posted_as_a_channel_is_removed_and_the_channel_banned(db):
    bot = FakeBot()
    message = FakeMessage(SPAM, sender_chat=channel())
    assert check_message(message, bot)
    assert message.deleted and bot.calls == [("ban_channel", CHANNEL)]
    incident = db.incidents[0]
    assert incident["user_id"] == CHANNEL and incident["action"] == Action.BAN  # Restore unbans
    report = bot.sent[0]
    assert "Crypto news" in report and "t.me" not in report and "href" not in report
    assert "posting as this channel is blocked" in report


def test_the_groups_own_channel_is_not_checked(db):
    message = FakeMessage(SPAM, sender_chat=channel("Our news"))
    assert not check_message(message, FakeBot(linked=CHANNEL))
    assert not message.deleted and db.member.trusted


# --- What happens to spam ---


def test_spam_that_cant_be_deleted_any_more_is_still_punished_and_reported(db):
    bot = FakeBot()  # has the right to delete: the message is too old or already gone
    message = FakeMessage(SPAM, delete_error="Bad Request: message can't be deleted")
    assert check_message(message, bot, edited=True)
    assert bot.calls == [("mute", 7)]
    assert "I couldn't delete the message" in bot.sent[0]
    assert "they are muted now" in bot.sent[0]
    assert db.stats == [(1, 1)]


def test_without_the_right_to_delete_the_bot_only_asks_for_it(db):
    bot = FakeBot(me=admin(delete=False))
    message = FakeMessage(SPAM, delete_error="Bad Request: message can't be deleted")
    assert not check_message(message, bot)
    assert bot.calls == [] and bot.sent == [EN.NEED_RIGHTS] and db.incidents == []


def test_a_failed_mute_is_reported_as_failed(db):
    bot = FakeBot(me=admin(restrict=False), refuse={"mute"})
    assert check_message(FakeMessage(SPAM), bot)
    assert "; couldn't mute them: give me the “Ban users” right" in bot.sent[0]
    assert "muted now" not in bot.sent[0]
    assert db.incidents[0]["action"] == Action.DELETE  # nothing for Restore to lift


def test_reports_carry_no_links_from_the_name_or_the_ai_reason(db):
    bot = FakeBot()
    verdict = AiVerdict(True, 95, "Ad for @spam_channel, join t.me/+x now", "haiku")
    assert check_message(FakeMessage(DOUBTFUL), bot, FakeClassifier(verdict))
    report = bot.sent[0]
    assert "Anna" in report and "t.me" not in report and "@spam_channel" not in report


def test_only_the_ai_puts_people_on_the_shared_spammer_list(db):
    assert check_message(FakeMessage(SPAM), FakeBot())  # the rules alone
    assert db.spammers == []
    verdict = AiVerdict(True, 95, "ad", "haiku")
    assert check_message(FakeMessage(DOUBTFUL), FakeBot(), FakeClassifier(verdict))
    assert db.spammers == [(7, GROUP)]


def test_clean_message_counts_towards_trust(db):
    assert not check_message(FakeMessage("Привет всем"), FakeBot())
    assert db.member.clean_messages == 1 and db.stats == [(1, 0)]


# --- The AI budget ---


def test_no_ai_checks_where_the_bot_cant_delete(db):
    classifier = FakeClassifier(AiVerdict(True, 95, "ad", "haiku"))
    assert not check_message(FakeMessage(DOUBTFUL), FakeBot(me=admin(delete=False)), classifier)
    assert classifier.calls == 0 and db.global_limits == []


def test_free_chats_leave_a_third_of_the_global_limit_for_pro(db):
    assert PLANS.free_global_limit == 1000
    classifier = FakeClassifier(AiVerdict(False, 90, "fine", "haiku"))
    check_message(FakeMessage(DOUBTFUL), FakeBot(), classifier)
    assert db.global_limits == [1000]


def test_one_person_gets_only_a_few_ai_checks_in_all_chats_together(monkeypatch):
    monkeypatch.setattr(guard, "_user_ai_checks", {})
    today = date(2026, 10, 30)
    assert all(guard.take_user_ai_check(7, today) for _ in range(guard.USER_AI_DAILY_LIMIT))
    assert not guard.take_user_ai_check(7, today)  # no chat gets another one today
    assert guard.take_user_ai_check(8, today)


# --- Rights ---


def test_rights_of():
    assert rights.rights_of(ChatMemberOwner.model_construct()) == Rights(delete=True, restrict=True)
    assert rights.rights_of(admin(restrict=False)) == Rights(delete=True, restrict=False)
    assert rights.rights_of(ChatMemberMember.model_construct()) == NO_RIGHTS

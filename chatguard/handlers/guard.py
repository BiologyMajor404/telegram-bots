"""The spam guard. Its router goes before every other one, so nothing slips past it: commands
with spam in the arguments, edited messages, media captions, posts made as a channel. A clean
message is passed on (SkipHandler) to the other handlers."""

import logging
import time
from contextlib import suppress
from dataclasses import dataclass
from datetime import UTC, date, datetime
from html import escape

from aiogram import Bot, F, Router
from aiogram.dispatcher.event.bases import SkipHandler
from aiogram.exceptions import TelegramAPIError, TelegramBadRequest, TelegramForbiddenError
from aiogram.types import ChatPermissions, Message
from sqlalchemy.ext.asyncio import AsyncSession

from chatguard import keyboards as kb
from chatguard import repo
from chatguard.ai import Classifier
from chatguard.config import Plans
from chatguard.decide import Decision, decide
from chatguard.models import Action, Chat, is_channel
from chatguard.reports import Outcome, mention, punishment_text, strip_links
from chatguard.rights import bot_rights
from chatguard.rules import check
from chatguard.texts import Ru
from shared.admins import is_admin
from shared.i18n import GROUP_CHATS

log = logging.getLogger(__name__)

router = Router(name="guard")
router.message.filter(F.chat.type.in_(GROUP_CHATS))
router.edited_message.filter(F.chat.type.in_(GROUP_CHATS))

NO_RIGHTS_NOTICE_SEC = 3600  # remind about missing admin rights at most once an hour
_no_rights_noticed: dict[int, float] = {}
# One person (or channel) can't drive more AI checks than this per day, in all chats together
USER_AI_DAILY_LIMIT = 5
_user_ai_checks: dict[tuple[int, date], int] = {}
USER_AI_KEYS_LIMIT = 10_000
LINKED_CHANNEL_SEC = 600  # a group's linked channel rarely changes
_linked_channels: dict[int, tuple[int | None, float]] = {}
# Longer messages are cut before they go to the AI: spam is obvious in the first part
AI_TEXT_LIMIT = 1500
NO_PERMISSIONS = ChatPermissions(
    can_send_messages=False,
    can_send_audios=False,
    can_send_documents=False,
    can_send_photos=False,
    can_send_videos=False,
    can_send_video_notes=False,
    can_send_voice_notes=False,
    can_send_polls=False,
    can_send_other_messages=False,
    can_add_web_page_previews=False,
)


@dataclass(frozen=True)
class Sender:
    id: int  # a person, or the channel someone posts as (chat ids are negative)
    name: str


@router.message()
async def new_message(
    message: Message,
    session: AsyncSession,
    bot: Bot,
    t: Ru,
    classifier: Classifier | None,
    plans: Plans,
) -> None:
    if not await guard(message, session, bot, t, classifier, plans, edited=False):
        raise SkipHandler  # clean: let the command handlers have it


@router.edited_message()
async def edited_message(
    message: Message,
    session: AsyncSession,
    bot: Bot,
    t: Ru,
    classifier: Classifier | None,
    plans: Plans,
) -> None:
    await guard(message, session, bot, t, classifier, plans, edited=True)


def message_signals(message: Message) -> dict:
    entities = (message.entities or []) + (message.caption_entities or [])
    origin = message.forward_origin
    return {
        "forwarded_from_channel": origin is not None and origin.type == "channel",
        "has_buttons": message.reply_markup is not None,
        "has_link_entities": any(e.type in ("url", "text_link") for e in entities),
    }


def sender_of(message: Message) -> Sender | None:
    """Whom a message is judged as, or None for senders the bot never checks: bots, service
    messages, anonymous admins (they post as the group itself) and the posts Telegram
    copies from a channel into its discussion group. Anyone can post as their own channel
    in a public group, so any other channel is checked like a person."""
    if message.sender_chat is not None:
        if message.sender_chat.id == message.chat.id or message.is_automatic_forward:
            return None
        return Sender(message.sender_chat.id, message.sender_chat.title or "")
    user = message.from_user
    if user is None or user.is_bot:
        return None
    return Sender(user.id, user.full_name)


def take_user_ai_check(sender_id: int, today: date) -> bool:
    key = (sender_id, today)
    if _user_ai_checks.get(key, 0) >= USER_AI_DAILY_LIMIT:
        return False
    if len(_user_ai_checks) > USER_AI_KEYS_LIMIT:  # drop old days, keep memory bounded
        for old in [k for k in _user_ai_checks if k[1] != today]:
            del _user_ai_checks[old]
    _user_ai_checks[key] = _user_ai_checks.get(key, 0) + 1
    return True


async def linked_channel(bot: Bot, chat_id: int) -> int | None:
    """The channel whose discussion group this chat is, if any."""
    now = time.monotonic()
    cached = _linked_channels.get(chat_id)
    if cached and now - cached[1] < LINKED_CHANNEL_SEC:
        return cached[0]
    try:
        linked = (await bot.get_chat(chat_id)).linked_chat_id
    except TelegramAPIError as e:
        log.warning("Can't read the linked channel of %s: %s", chat_id, e)
        return None
    _linked_channels[chat_id] = (linked, now)
    return linked


async def speaks_for_chat(bot: Bot, chat_id: int, sender_id: int) -> bool:
    """Admins, and the channel whose discussion group this is: the bot doesn't check them."""
    if is_channel(sender_id):
        return sender_id == await linked_channel(bot, chat_id)
    return await is_admin(bot, chat_id, sender_id)


async def who_to_check(
    message: Message, session: AsyncSession, bot: Bot, *, edited: bool
) -> tuple[Chat, Sender] | None:
    """The chat and the sender if this message needs checking, None if it doesn't."""
    sender = sender_of(message)
    if sender is None:
        return None
    if not (message.text or message.caption) and not any(message_signals(message).values()):
        return None  # a plain photo or sticker: nothing to judge
    chat = await repo.ensure_chat(session, message.chat.id, message.chat.title)
    if not chat.enabled:
        return None
    member = await repo.get_member(session, chat.id, sender.id)
    # Three clean messages earn trust for new messages, but edits are checked until an
    # admin vouches: "hi" edited into an ad afterwards is a common trick
    if member.trusted or (not edited and not repo.needs_check(member)):
        return None
    if await speaks_for_chat(bot, chat.id, sender.id):
        member.trusted = True
        await session.commit()
        return None
    return chat, sender


async def guard(
    message: Message,
    session: AsyncSession,
    bot: Bot,
    t: Ru,
    classifier: Classifier | None,
    plans: Plans,
    *,
    edited: bool,
) -> bool:
    """Check a message; True if it was spam and has been dealt with."""
    target = await who_to_check(message, session, bot, edited=edited)
    if target is None:
        return False
    chat, sender = target
    text = message.text or message.caption or ""
    signals = message_signals(message)

    now = datetime.now(UTC)
    today = now.date()
    pro = repo.is_pro(chat, now)
    known = pro and await repo.is_known_spammer(session, sender.id)
    rules = check(text, **signals, known_spammer=known)

    async def reserve_ai() -> bool:
        # Not where the bot couldn't delete the spam anyway; then per person (in all chats
        # together), per chat, and for the whole bot, where free chats leave a share for Pro.
        # Each reservation is atomic
        return (
            (await bot_rights(bot, chat.id)).delete
            and take_user_ai_check(sender.id, today)
            and await repo.reserve_ai_check(
                session, chat.id, today, repo.ai_limit(chat, now, plans)
            )
            and await repo.reserve_global_ai_check(
                session, today, plans.global_limit if pro else plans.free_global_limit
            )
        )

    ai_text = text[:AI_TEXT_LIMIT] if text else ""
    decision = await decide(
        ai_text, rules, chat.lang, classifier if text else None, reserve_ai, allow_opus=pro
    )
    if not decision.is_spam:
        # Only real text counts towards trust; captionless media or edits don't
        if text and not edited:
            await repo.count_clean(session, chat.id, sender.id)
        await repo.bump_stats(session, chat.id, checked=1)
        await session.commit()
        return False
    return await remove_spam(message, session, bot, t, chat, sender, text, decision, now)


async def remove_spam(
    message: Message,
    session: AsyncSession,
    bot: Bot,
    t: Ru,
    chat: Chat,
    sender: Sender,
    text: str,
    decision: Decision,
    now: datetime,
) -> bool:
    """Delete, punish, record and report. The Telegram calls come first, so the chat's row
    isn't locked (by bump_stats) while they wait."""
    deleted = await delete_spam(message, bot)
    if deleted is None:
        await repo.bump_stats(session, chat.id, checked=1)
        await session.commit()
        await notify_no_rights(bot, chat.id, t)
        return False
    punished = await punish(bot, chat, sender.id)
    # The hint about the right only when that's the cause: e.g. a basic group can't mute at all
    need_right = not punished and not (await bot_rights(bot, chat.id, fresh=True)).restrict
    await repo.bump_stats(session, chat.id, checked=1, caught=1)
    if decision.source != "rules":
        # Only the AI's verdict is sure enough to follow someone into other chats
        await repo.record_spammer(session, sender.id, chat.id, now)
    await report(
        bot, session, chat, t, sender, text, decision, Outcome(deleted, punished, need_right)
    )
    return True


async def delete_spam(message: Message, bot: Bot) -> bool | None:
    """True if deleted; False if it can't be any more (older than 48 hours, or someone was
    quicker); None if the bot has no right to delete messages here."""
    try:
        await message.delete()
    except TelegramForbiddenError:  # the bot is no longer in the chat
        return None
    except TelegramBadRequest:
        # Telegram answers "can't be deleted" both to an old message and to missing rights
        return False if (await bot_rights(bot, message.chat.id, fresh=True)).delete else None
    return True


def applied_action(action: str, punished: bool, channel: bool) -> str:
    """What Restore will have to undo: nothing if punishing failed, and a ban for a channel,
    which can't be muted."""
    if action == Action.DELETE or not punished:
        return Action.DELETE
    return Action.BAN if channel else action


async def report(
    bot: Bot,
    session: AsyncSession,
    chat: Chat,
    t: Ru,
    sender: Sender,
    text: str,
    decision: Decision,
    outcome: Outcome,
) -> None:
    if decision.source == "rules":
        signals = ", ".join(t.SIGNALS.get(r, r) for r in decision.rules.reasons)
        reason, source = t.REASON_RULES.format(signals=signals), t.SOURCE_RULES
    else:
        reason = strip_links(decision.reason)
        source = f"{t.SOURCE_AI} {decision.source.capitalize()}"
    channel = is_channel(sender.id)
    incident = await repo.add_incident(
        session,
        chat_id=chat.id,
        user_id=sender.id,
        user_name=sender.name[:128],
        text=text[:4000],
        source=decision.source,
        reason=reason[:500],
        action=applied_action(chat.action, outcome.punished, channel),
    )
    await bot.send_message(
        chat.id,
        (t.REPORT if outcome.deleted else t.REPORT_KEPT).format(
            user=mention(sender.id, sender.name),
            punishment=punishment_text(t, chat.action, channel, outcome),
            source=source,
            reason=escape(reason),
        ),
        reply_markup=kb.restore(t, incident.id),
    )


async def notify_no_rights(bot: Bot, chat_id: int, t: Ru) -> None:
    now = time.monotonic()
    if now - _no_rights_noticed.get(chat_id, -NO_RIGHTS_NOTICE_SEC) < NO_RIGHTS_NOTICE_SEC:
        return
    _no_rights_noticed[chat_id] = now
    with suppress(TelegramBadRequest, TelegramForbiddenError):
        await bot.send_message(chat_id, t.NEED_RIGHTS)


async def punish(bot: Bot, chat: Chat, sender_id: int) -> bool:
    """Mute or ban as the chat is set up; False if Telegram refused. A channel can't be
    muted: posting as it is banned instead."""
    if chat.action == Action.DELETE:
        return True
    try:
        if is_channel(sender_id):
            await bot.ban_chat_sender_chat(chat.id, sender_id)
        elif chat.action == Action.MUTE:
            await bot.restrict_chat_member(chat.id, sender_id, permissions=NO_PERMISSIONS)
        else:
            await bot.ban_chat_member(chat.id, sender_id)
    except TelegramAPIError as e:
        log.warning("Can't punish %s in %s: %s", sender_id, chat.id, e)
        return False
    return True

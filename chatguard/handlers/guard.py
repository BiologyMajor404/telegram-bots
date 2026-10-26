"""The spam guard. Its router runs before every other group handler, so nothing slips past
it: commands with spam in the arguments, edited messages, media captions. A clean message
is passed on (SkipHandler) to the command handlers."""

import logging
import time
from contextlib import suppress
from datetime import UTC, date, datetime
from html import escape

from aiogram import Bot, F, Router
from aiogram.dispatcher.event.bases import SkipHandler
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from aiogram.types import ChatPermissions, Message
from sqlalchemy.ext.asyncio import AsyncSession

from chatguard import keyboards as kb
from chatguard import repo
from chatguard.ai import Classifier
from chatguard.config import Plans
from chatguard.decide import Decision, decide
from chatguard.models import Action, Chat, Member
from chatguard.rules import check
from chatguard.texts import Ru
from shared.admins import is_admin
from shared.formatting import user_link
from shared.i18n import GROUP_CHATS

log = logging.getLogger(__name__)

router = Router(name="guard")
router.message.filter(F.chat.type.in_(GROUP_CHATS))
router.edited_message.filter(F.chat.type.in_(GROUP_CHATS))

NO_RIGHTS_NOTICE_SEC = 3600  # remind about missing admin rights at most once an hour
_no_rights_noticed: dict[int, float] = {}
# One person can't drive more AI checks than this per chat per day
USER_AI_DAILY_LIMIT = 5
_user_ai_checks: dict[tuple[int, int, date], int] = {}
USER_AI_KEYS_LIMIT = 10_000
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


def take_user_ai_check(chat_id: int, user_id: int, today: date) -> bool:
    key = (chat_id, user_id, today)
    if _user_ai_checks.get(key, 0) >= USER_AI_DAILY_LIMIT:
        return False
    if len(_user_ai_checks) > USER_AI_KEYS_LIMIT:  # drop old days, keep memory bounded
        for old in [k for k in _user_ai_checks if k[2] != today]:
            del _user_ai_checks[old]
    _user_ai_checks[key] = _user_ai_checks.get(key, 0) + 1
    return True


async def who_to_check(
    message: Message, session: AsyncSession, bot: Bot, *, edited: bool
) -> tuple[Chat, Member] | None:
    """The chat and the sender if this message needs checking, None if it doesn't."""
    user = message.from_user
    # Channels and anonymous admins post as sender_chat; bots and service messages are skipped
    if user is None or user.is_bot or message.sender_chat is not None:
        return None
    if not (message.text or message.caption) and not any(message_signals(message).values()):
        return None  # a plain photo or sticker: nothing to judge
    chat = await repo.ensure_chat(session, message.chat.id, message.chat.title)
    if not chat.enabled:
        return None
    member = await repo.get_member(session, chat.id, user.id)
    # Three clean messages earn trust for new messages, but edits are checked until an
    # admin vouches: "hi" edited into an ad afterwards is a common trick
    if member.trusted or (not edited and not repo.needs_check(member)):
        return None
    if await is_admin(bot, chat.id, user.id):
        member.trusted = True
        await session.commit()
        return None
    return chat, member


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
    """Check a message; True if it was spam and has been removed."""
    target = await who_to_check(message, session, bot, edited=edited)
    if target is None:
        return False
    chat, member = target
    user = message.from_user
    text = message.text or message.caption or ""
    signals = message_signals(message)

    now = datetime.now(UTC)
    today = now.date()
    pro = repo.is_pro(chat, now)
    known = pro and await repo.is_known_spammer(session, user.id)
    rules = check(text, **signals, known_spammer=known)

    async def reserve_ai() -> bool:
        # Per person, per chat, then for the whole bot; each reservation is atomic
        return (
            take_user_ai_check(chat.id, user.id, today)
            and await repo.reserve_ai_check(
                session, chat.id, today, repo.ai_limit(chat, now, plans)
            )
            and await repo.reserve_global_ai_check(session, today, plans.global_limit)
        )

    ai_text = text[:AI_TEXT_LIMIT] if text else ""
    decision = await decide(
        ai_text, rules, chat.lang, classifier if text else None, reserve_ai, allow_opus=pro
    )
    await repo.bump_stats(session, chat.id, checked=1)

    if not decision.is_spam:
        # Only real text counts towards trust; captionless media or edits don't
        if text and not edited:
            member.clean_messages += 1
        await session.commit()
        return False

    try:
        await message.delete()
    except (TelegramBadRequest, TelegramForbiddenError):
        await session.commit()
        await notify_no_rights(bot, chat.id, t)
        return False
    await punish(bot, chat, user.id)
    await repo.bump_stats(session, chat.id, caught=1)
    await repo.record_spammer(session, user.id, now)
    await report(bot, session, chat, t, user.id, user.full_name, text, decision)
    return True


async def report(
    bot: Bot,
    session: AsyncSession,
    chat: Chat,
    t: Ru,
    user_id: int,
    name: str,
    text: str,
    decision: Decision,
) -> None:
    if decision.source == "rules":
        signals = ", ".join(t.SIGNALS.get(r, r) for r in decision.rules.reasons)
        reason, source = t.REASON_RULES.format(signals=signals), t.SOURCE_RULES
    else:
        reason, source = decision.reason, f"{t.SOURCE_AI} {decision.source.capitalize()}"
    incident = await repo.add_incident(
        session,
        chat_id=chat.id,
        user_id=user_id,
        user_name=name[:128],
        text=text[:4000],
        source=decision.source,
        reason=reason[:500],
        action=chat.action,
    )
    punishment = {
        Action.DELETE: t.PUNISH_DELETE,
        Action.MUTE: t.PUNISH_MUTE,
        Action.BAN: t.PUNISH_BAN,
    }[chat.action]
    await bot.send_message(
        chat.id,
        t.REPORT.format(
            user=user_link(user_id, name),
            punishment=punishment,
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


async def punish(bot: Bot, chat: Chat, user_id: int) -> None:
    try:
        if chat.action == Action.MUTE:
            await bot.restrict_chat_member(chat.id, user_id, permissions=NO_PERMISSIONS)
        elif chat.action == Action.BAN:
            await bot.ban_chat_member(chat.id, user_id)
    except (TelegramBadRequest, TelegramForbiddenError) as e:
        log.warning("Can't punish %s in %s: %s", user_id, chat.id, e)

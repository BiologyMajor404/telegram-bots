import logging
import time
from contextlib import suppress
from datetime import UTC, datetime
from html import escape

from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from aiogram.filters import JOIN_TRANSITION, ChatMemberUpdatedFilter, Command
from aiogram.types import CallbackQuery, ChatMemberUpdated, ChatPermissions, Message
from sqlalchemy.ext.asyncio import AsyncSession

from chatguard import keyboards as kb
from chatguard import repo
from chatguard.admins import is_admin
from chatguard.ai import Classifier
from chatguard.config import Plans
from chatguard.decide import decide
from chatguard.handlers.payments import fmt_date, pro_offer
from chatguard.i18n import GROUPS
from chatguard.models import Action, Chat
from chatguard.rules import check
from chatguard.texts import TEXTS, Ru, user_link
from shared.i18n import CHOOSE_LANGUAGE, SetLang, lang_keyboard

log = logging.getLogger(__name__)

router = Router(name="group")
router.message.filter(F.chat.type.in_(GROUPS))
router.callback_query.filter(F.message.chat.type.in_(GROUPS))
router.my_chat_member.filter(F.chat.type.in_(GROUPS))

NO_RIGHTS_NOTICE_SEC = 3600  # remind about missing admin rights at most once an hour
_no_rights_noticed: dict[int, float] = {}
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


@router.my_chat_member(ChatMemberUpdatedFilter(JOIN_TRANSITION))
async def bot_added(event: ChatMemberUpdated, bot: Bot, t: Ru) -> None:
    await bot.send_message(event.chat.id, t.WELCOME_GROUP)


@router.message(Command("start", "help"))
async def help_cmd(message: Message, t: Ru) -> None:
    await message.answer(t.WELCOME_GROUP)


# --- Settings (admins only) ---


def ai_status(t: Ru, chat: Chat, classifier: Classifier | None, plans: Plans) -> str:
    now = datetime.now(UTC)
    if classifier is None:
        return t.AI_OFF
    if not repo.ai_budget_left(chat, now.date(), repo.ai_limit(chat, now, plans)):
        return t.AI_LIMIT
    return t.AI_ON_PRO if repo.is_pro(chat, now) else t.AI_ON_FREE


def settings_text(t: Ru, chat: Chat, classifier: Classifier | None, plans: Plans) -> str:
    actions = {Action.DELETE: t.ACTION_DELETE, Action.MUTE: t.ACTION_MUTE, Action.BAN: t.ACTION_BAN}
    pro = repo.is_pro(chat, datetime.now(UTC))
    return t.SETTINGS.format(
        plan=t.PLAN_PRO.format(until=fmt_date(chat.pro_until)) if pro else t.PLAN_FREE,
        status=t.STATUS_ON if chat.enabled else t.STATUS_OFF,
        action=actions[chat.action],
        ai=ai_status(t, chat, classifier, plans),
        checked=chat.checked,
        caught=chat.caught,
    )


@router.message(Command("settings"))
async def settings_cmd(
    message: Message,
    session: AsyncSession,
    bot: Bot,
    t: Ru,
    classifier: Classifier | None,
    plans: Plans,
) -> None:
    if not await is_admin(bot, message.chat.id, message.from_user.id):
        await message.reply(t.ONLY_ADMINS)
        return
    chat = await repo.ensure_chat(session, message.chat.id, message.chat.title)
    await message.answer(
        settings_text(t, chat, classifier, plans), reply_markup=kb.settings(t, chat)
    )


@router.callback_query(kb.Setting.filter())
async def settings_change(
    cb: CallbackQuery,
    callback_data: kb.Setting,
    session: AsyncSession,
    bot: Bot,
    t: Ru,
    classifier: Classifier | None,
    plans: Plans,
) -> None:
    if not await is_admin(bot, cb.message.chat.id, cb.from_user.id):
        await cb.answer(t.ONLY_ADMINS, show_alert=True)
        return
    chat = await repo.ensure_chat(session, cb.message.chat.id, cb.message.chat.title)
    if callback_data.name == "lang":
        await cb.message.answer(CHOOSE_LANGUAGE, reply_markup=lang_keyboard())
        await cb.answer()
        return
    if callback_data.name == "pro":
        text, markup = await pro_offer(bot, chat, t, plans)
        await cb.message.answer(text, reply_markup=markup)
        await cb.answer()
        return
    if callback_data.name == "action" and callback_data.value in Action.ALL:
        chat.action = callback_data.value
    elif callback_data.name == "toggle":
        chat.enabled = not chat.enabled
    await session.commit()
    await cb.message.edit_text(
        settings_text(t, chat, classifier, plans), reply_markup=kb.settings(t, chat)
    )
    await cb.answer()


@router.message(Command("pro"))
async def pro_cmd(message: Message, session: AsyncSession, bot: Bot, t: Ru, plans: Plans) -> None:
    if not await is_admin(bot, message.chat.id, message.from_user.id):
        await message.reply(t.ONLY_ADMINS)
        return
    chat = await repo.ensure_chat(session, message.chat.id, message.chat.title)
    text, markup = await pro_offer(bot, chat, t, plans)
    await message.answer(text, reply_markup=markup)


@router.message(Command("language"))
async def language_cmd(message: Message, bot: Bot, t: Ru) -> None:
    if not await is_admin(bot, message.chat.id, message.from_user.id):
        await message.reply(t.ONLY_ADMINS)
        return
    await message.answer(CHOOSE_LANGUAGE, reply_markup=lang_keyboard())


@router.callback_query(SetLang.filter())
async def set_language(
    cb: CallbackQuery, callback_data: SetLang, session: AsyncSession, bot: Bot, t: Ru
) -> None:
    new_t = TEXTS.get(callback_data.code)
    if new_t is None:
        await cb.answer()
        return
    if not await is_admin(bot, cb.message.chat.id, cb.from_user.id):
        await cb.answer(t.ONLY_ADMINS, show_alert=True)
        return
    chat = await repo.ensure_chat(session, cb.message.chat.id, cb.message.chat.title)
    chat.lang = new_t.LANG
    await session.commit()
    await cb.message.edit_text(new_t.LANGUAGE_SET)
    await cb.answer()


# --- Restoring a wrongly removed person ---


@router.callback_query(kb.Restore.filter())
async def restore(
    cb: CallbackQuery, callback_data: kb.Restore, session: AsyncSession, bot: Bot, t: Ru
) -> None:
    if not await is_admin(bot, cb.message.chat.id, cb.from_user.id):
        await cb.answer(t.ONLY_ADMINS, show_alert=True)
        return
    incident = await repo.get_incident(session, callback_data.incident)
    if incident is None or incident.chat_id != cb.message.chat.id:
        await cb.answer()
        return
    if incident.restored:
        await cb.answer(t.ALREADY_RESTORED)
        return
    try:
        if incident.action == Action.BAN:
            await bot.unban_chat_member(incident.chat_id, incident.user_id, only_if_banned=True)
        elif incident.action == Action.MUTE:
            # Back to the group's default permissions
            group = await bot.get_chat(incident.chat_id)
            await bot.restrict_chat_member(
                incident.chat_id, incident.user_id, permissions=group.permissions
            )
    except (TelegramBadRequest, TelegramForbiddenError) as e:
        log.warning("Can't lift the punishment in %s: %s", incident.chat_id, e)
    await repo.restore(session, incident)
    await cb.message.edit_text(
        t.RESTORED.format(
            admin=user_link(cb.from_user.id, cb.from_user.full_name),
            user=user_link(incident.user_id, incident.user_name),
            text=escape(incident.text),
        )
    )
    await cb.answer()


# --- The guard itself: every other message in the group ---


def message_signals(message: Message) -> dict:
    entities = (message.entities or []) + (message.caption_entities or [])
    origin = message.forward_origin
    return {
        "forwarded_from_channel": origin is not None and origin.type == "channel",
        "has_buttons": message.reply_markup is not None,
        "has_link_entities": any(e.type in ("url", "text_link") for e in entities),
    }


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


@router.message()
async def guard(
    message: Message,
    session: AsyncSession,
    bot: Bot,
    t: Ru,
    classifier: Classifier | None,
    plans: Plans,
) -> None:
    user = message.from_user
    text = message.text or message.caption or ""
    # Channels and anonymous admins post as sender_chat; bots and service messages are skipped
    if user is None or user.is_bot or message.sender_chat is not None or not text:
        return
    chat = await repo.ensure_chat(session, message.chat.id, message.chat.title)
    if not chat.enabled:
        return
    member = await repo.get_member(session, chat.id, user.id)
    if not repo.needs_check(member):
        return
    if await is_admin(bot, chat.id, user.id):
        member.trusted = True
        await session.commit()
        return

    now = datetime.now(UTC)
    today = now.date()
    pro = repo.is_pro(chat, now)
    known = pro and await repo.is_known_spammer(session, user.id)
    rules = check(text, **message_signals(message), known_spammer=known)
    ai_allowed = repo.ai_budget_left(chat, today, repo.ai_limit(chat, now, plans))
    decision = await decide(text, rules, chat.lang, classifier, ai_allowed, allow_opus=pro)
    if decision.source in ("haiku", "opus"):
        repo.spend_ai_check(chat, today)
    chat.checked += 1

    if not decision.is_spam:
        member.clean_messages += 1
        await session.commit()
        return

    try:
        await message.delete()
    except (TelegramBadRequest, TelegramForbiddenError):
        await session.commit()
        await notify_no_rights(bot, chat.id, t)
        return
    await punish(bot, chat, user.id)
    chat.caught += 1
    await repo.record_spammer(session, user.id, now)

    if decision.source == "rules":
        signals = ", ".join(t.SIGNALS.get(r, r) for r in decision.rules.reasons)
        reason, source = t.REASON_RULES.format(signals=signals), t.SOURCE_RULES
    else:
        reason, source = decision.reason, f"{t.SOURCE_AI} {decision.source.capitalize()}"
    incident = await repo.add_incident(
        session,
        chat_id=chat.id,
        user_id=user.id,
        user_name=user.full_name[:128],
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
            user=user_link(user.id, user.full_name),
            punishment=punishment,
            source=source,
            reason=escape(reason),
        ),
        reply_markup=kb.restore(t, incident.id),
    )

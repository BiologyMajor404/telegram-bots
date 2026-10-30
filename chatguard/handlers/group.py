"""Group chats: welcome, admin settings, Pro offer, language and restoring people.
The spam check itself lives in handlers/guard.py and runs before these handlers."""

import logging
from datetime import UTC, datetime

from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from aiogram.filters import JOIN_TRANSITION, ChatMemberUpdatedFilter, Command, CommandObject
from aiogram.types import CallbackQuery, ChatMemberUpdated, Message
from sqlalchemy.ext.asyncio import AsyncSession

from chatguard import keyboards as kb
from chatguard import repo
from chatguard.ai import Classifier
from chatguard.config import Plans
from chatguard.handlers.payments import fmt_date, pro_offer
from chatguard.models import Action, Chat, Incident, is_channel
from chatguard.reports import restored_text
from chatguard.rights import can_restore
from chatguard.texts import TEXTS, Ru
from shared.admins import is_admin, sender_is_admin
from shared.i18n import CHOOSE_LANGUAGE, GROUP_CHATS, SetLang, lang_keyboard

log = logging.getLogger(__name__)

router = Router(name="group")
router.message.filter(F.chat.type.in_(GROUP_CHATS))
router.callback_query.filter(F.message.chat.type.in_(GROUP_CHATS))
router.my_chat_member.filter(F.chat.type.in_(GROUP_CHATS))


@router.my_chat_member(ChatMemberUpdatedFilter(JOIN_TRANSITION))
async def bot_added(event: ChatMemberUpdated, bot: Bot, t: Ru) -> None:
    await bot.send_message(event.chat.id, t.WELCOME_GROUP)


@router.message(Command("start"))
async def start_cmd(message: Message, command: CommandObject, t: Ru) -> None:
    # Telegram hands a bare /start in a group to whichever bot spoke last, so it may be
    # meant for another bot: answer only /start@this_bot (joining is greeted separately)
    if command.mention is not None:
        await message.answer(t.WELCOME_GROUP)


@router.message(Command("help"))
async def help_cmd(message: Message, t: Ru) -> None:
    await message.answer(t.WELCOME_GROUP)


# --- A group becoming a supergroup (it gets a new id; Telegram tells both chats) ---


@router.message(F.migrate_to_chat_id)
async def migrated_to(message: Message, session: AsyncSession) -> None:
    await repo.migrate_chat(session, message.chat.id, message.migrate_to_chat_id)


@router.message(F.migrate_from_chat_id)
async def migrated_from(message: Message, session: AsyncSession) -> None:
    await repo.migrate_chat(session, message.migrate_from_chat_id, message.chat.id)


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
    if not await sender_is_admin(bot, message):
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
    if not await sender_is_admin(bot, message):
        await message.reply(t.ONLY_ADMINS)
        return
    chat = await repo.ensure_chat(session, message.chat.id, message.chat.title)
    text, markup = await pro_offer(bot, chat, t, plans)
    await message.answer(text, reply_markup=markup)


@router.message(Command("language"))
async def language_cmd(message: Message, bot: Bot, t: Ru) -> None:
    if not await sender_is_admin(bot, message):
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
    if not await can_restore(bot, cb.message.chat.id, cb.from_user.id):
        await cb.answer(t.RESTORE_NEEDS_RIGHT, show_alert=True)
        return
    incident = await repo.get_incident(session, callback_data.incident)
    if incident is None or incident.chat_id != cb.message.chat.id:
        await cb.answer()
        return
    if incident.restored:
        await cb.answer(t.ALREADY_RESTORED)
        return
    await lift_punishment(bot, incident)
    await repo.restore(session, incident)
    await cb.message.edit_text(
        restored_text(
            t,
            cb.from_user.id,
            cb.from_user.full_name,
            incident.user_id,
            incident.user_name,
            incident.text,
        )
    )
    await cb.answer()


async def lift_punishment(bot: Bot, incident: Incident) -> None:
    """Undo the mute or ban; if Telegram refuses (e.g. the bot lost its rights), only log it."""
    try:
        if incident.action == Action.DELETE:
            return
        if is_channel(incident.user_id):  # someone posted as a channel: the channel was banned
            await bot.unban_chat_sender_chat(incident.chat_id, incident.user_id)
        elif incident.action == Action.BAN:
            await bot.unban_chat_member(incident.chat_id, incident.user_id, only_if_banned=True)
        else:
            # Back to the group's default permissions
            group = await bot.get_chat(incident.chat_id)
            await bot.restrict_chat_member(
                incident.chat_id, incident.user_id, permissions=group.permissions
            )
    except (TelegramBadRequest, TelegramForbiddenError) as e:
        log.warning("Can't lift the punishment in %s: %s", incident.chat_id, e)

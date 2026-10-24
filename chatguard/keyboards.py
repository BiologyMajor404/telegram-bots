from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from chatguard.models import Action, Chat
from chatguard.texts import Ru
from shared.i18n import LANGUAGE_BUTTON

# Prefixes are short: Telegram limits callback data to 64 bytes


class Restore(CallbackData, prefix="r"):
    incident: int


class Setting(CallbackData, prefix="cfg"):
    name: str  # action | toggle | lang | pro
    value: str = ""


def add_as_admin(t: Ru, bot_username: str) -> InlineKeyboardMarkup:
    # `admin=` asks Telegram to pre-select these rights in the "add to group" dialog
    url = f"https://t.me/{bot_username}?startgroup=start&admin=delete_messages+restrict_members"
    b = InlineKeyboardBuilder()
    b.button(text=t.BTN_ADD_TO_GROUP, url=url)
    return b.as_markup()


def restore(t: Ru, incident_id: int) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text=t.BTN_RESTORE, callback_data=Restore(incident=incident_id))
    return b.as_markup()


def settings(t: Ru, chat: Chat) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    labels = {
        Action.DELETE: t.BTN_ACTION_DELETE,
        Action.MUTE: t.BTN_ACTION_MUTE,
        Action.BAN: t.BTN_ACTION_BAN,
    }
    for action in Action.ALL:
        mark = "• " if chat.action == action else ""
        b.button(text=f"{mark}{labels[action]}", callback_data=Setting(name="action", value=action))
    b.button(
        text=t.BTN_TURN_OFF if chat.enabled else t.BTN_TURN_ON,
        callback_data=Setting(name="toggle"),
    )
    b.button(text=t.BTN_PRO, callback_data=Setting(name="pro"))
    b.button(text=LANGUAGE_BUTTON, callback_data=Setting(name="lang"))
    b.adjust(1)
    return b.as_markup()

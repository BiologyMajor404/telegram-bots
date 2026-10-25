"""Inline keyboards and their callback data."""

from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from splitmate.models import Member
from splitmate.money import Transfer, fmt_money
from splitmate.texts import Ru

# Prefixes are short: Telegram limits callback data to 64 bytes


class Join(CallbackData, prefix="j"):
    pass


class ExpenseAction(CallbackData, prefix="e"):
    action: str  # people | amounts | equal | delete | done
    id: int


class MeToo(CallbackData, prefix="mt"):
    expense: int


class PickShare(CallbackData, prefix="ps"):
    expense: int
    user: int


class Toggle(CallbackData, prefix="p"):
    expense: int
    user: int


class SetCurrency(CallbackData, prefix="cur"):
    symbol: str


# Most used currencies of the bot's audience: (symbol shown in amounts, ISO code)
POPULAR_CURRENCIES = [
    ("₴", "UAH"),
    ("zł", "PLN"),
    ("€", "EUR"),
    ("$", "USD"),
    ("£", "GBP"),
    ("Kč", "CZK"),
    ("₸", "KZT"),
    ("₾", "GEL"),
    ("₺", "TRY"),
    ("₽", "RUB"),
]


class Settle(CallbackData, prefix="st"):
    debtor: int
    creditor: int


def add_to_group(t: Ru, bot_username: str) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text=t.BTN_ADD_TO_GROUP, url=f"https://t.me/{bot_username}?startgroup=start")
    return b.as_markup()


def join(t: Ru) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text=t.BTN_JOIN, callback_data=Join())
    return b.as_markup()


def expense(t: Ru, expense_id: int) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text=t.BTN_PEOPLE, callback_data=ExpenseAction(action="people", id=expense_id))
    b.button(text=t.BTN_AMOUNTS, callback_data=ExpenseAction(action="amounts", id=expense_id))
    b.button(text=t.BTN_ME_TOO, callback_data=MeToo(expense=expense_id))
    b.button(text=t.BTN_DELETE, callback_data=ExpenseAction(action="delete", id=expense_id))
    b.adjust(2, 2)
    return b.as_markup()


def amounts(
    t: Ru, expense_id: int, rows: list[tuple[int, str, int, bool]], currency: str
) -> InlineKeyboardMarkup:
    """rows: (user_id, name, share, set by hand)"""
    b = InlineKeyboardBuilder()
    for uid, person, share, fixed in rows:
        pin = "📌 " if fixed else ""
        b.button(
            text=f"{pin}{person}: {fmt_money(share, currency)}",
            callback_data=PickShare(expense=expense_id, user=uid),
        )
    b.button(text=t.BTN_EQUAL, callback_data=ExpenseAction(action="equal", id=expense_id))
    b.button(text=t.BTN_DONE, callback_data=ExpenseAction(action="done", id=expense_id))
    b.adjust(*[1] * len(rows), 2)
    return b.as_markup()


def participants(
    t: Ru, expense_id: int, people: list[Member], selected: set[int]
) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for m in people:
        mark = "✅" if m.user_id in selected else "▫️"
        b.button(text=f"{mark} {m.name}", callback_data=Toggle(expense=expense_id, user=m.user_id))
    b.button(text=t.BTN_DONE, callback_data=ExpenseAction(action="done", id=expense_id))
    b.adjust(2)
    return b.as_markup()


def settle(transfers: list[Transfer], names: dict[int, str], currency: str) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for debtor, creditor, amount in transfers[:20]:
        b.button(
            text=f"✅ {names.get(debtor, '?')} → {names.get(creditor, '?')} "
            f"{fmt_money(amount, currency)}",
            callback_data=Settle(debtor=debtor, creditor=creditor),
        )
    b.adjust(1)
    return b.as_markup()


def currencies() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for symbol, code in POPULAR_CURRENCIES:
        b.button(text=f"{symbol} {code}", callback_data=SetCurrency(symbol=symbol))
    b.adjust(2)
    return b.as_markup()

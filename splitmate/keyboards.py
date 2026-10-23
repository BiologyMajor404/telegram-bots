from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from splitmate.models import Member
from splitmate.money import Transfer, fmt_money

# Prefixes are short: Telegram limits callback data to 64 bytes


class Join(CallbackData, prefix="j"):
    pass


class ExpenseAction(CallbackData, prefix="e"):
    action: str  # people | delete | done
    id: int


class Toggle(CallbackData, prefix="p"):
    expense: int
    user: int


class Settle(CallbackData, prefix="st"):
    debtor: int
    creditor: int


def add_to_group(bot_username: str) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="➕ Добавить в группу", url=f"https://t.me/{bot_username}?startgroup=start")
    return b.as_markup()


def join() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="🙋 Я участвую", callback_data=Join())
    return b.as_markup()


def expense(expense_id: int) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="👥 Кто участвует", callback_data=ExpenseAction(action="people", id=expense_id))
    b.button(text="🗑 Удалить", callback_data=ExpenseAction(action="delete", id=expense_id))
    return b.as_markup()


def participants(expense_id: int, people: list[Member], selected: set[int]) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for m in people:
        mark = "✅" if m.user_id in selected else "▫️"
        b.button(text=f"{mark} {m.name}", callback_data=Toggle(expense=expense_id, user=m.user_id))
    b.button(text="Готово", callback_data=ExpenseAction(action="done", id=expense_id))
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

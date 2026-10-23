from datetime import date, datetime
from zoneinfo import ZoneInfo

from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from slotbook import texts
from slotbook.models import Booking, Service

# --- Callback data. Prefixes are short: Telegram limits callback data to 64 bytes ---


class Menu(CallbackData, prefix="m"):
    action: str  # home | book | my


class Svc(CallbackData, prefix="s"):
    id: int


class Day(CallbackData, prefix="d"):
    svc: int
    day: int  # YYYYMMDD


class Slot(CallbackData, prefix="t"):
    svc: int
    ts: int  # unix timestamp of the slot start


class Confirm(CallbackData, prefix="c"):
    svc: int
    ts: int


class CancelBooking(CallbackData, prefix="x"):
    id: int


class Admin(CallbackData, prefix="a"):
    action: str
    id: int = 0


def day_to_int(d: date) -> int:
    return d.year * 10000 + d.month * 100 + d.day


def int_to_day(v: int) -> date:
    return date(v // 10000, v // 100 % 100, v % 100)


# --- Client keyboards ---


def main_menu(is_admin: bool) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="📅 Записаться", callback_data=Menu(action="book"))
    b.button(text="🗂 Мои записи", callback_data=Menu(action="my"))
    if is_admin:
        b.button(text="⚙️ Панель мастера", callback_data=Admin(action="menu"))
    b.adjust(1)
    return b.as_markup()


def back_home() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="◀️ В меню", callback_data=Menu(action="home"))
    return b.as_markup()


def services(items: list[Service]) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for s in items:
        b.button(text=f"{s.name} · {s.price} ₽", callback_data=Svc(id=s.id))
    b.button(text="◀️ В меню", callback_data=Menu(action="home"))
    b.adjust(1)
    return b.as_markup()


def days(service_id: int, items: list[date]) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for d in items:
        b.button(text=texts.fmt_day(d), callback_data=Day(svc=service_id, day=day_to_int(d)))
    b.adjust(2)
    b.row(InlineKeyboardButton(text="◀️ Услуги", callback_data=Menu(action="book").pack()))
    return b.as_markup()


def times(service_id: int, slots: list[datetime], tz: ZoneInfo) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for t in slots:
        b.button(
            text=t.astimezone(tz).strftime("%H:%M"),
            callback_data=Slot(svc=service_id, ts=int(t.timestamp())),
        )
    b.adjust(4)
    b.row(InlineKeyboardButton(text="◀️ Дни", callback_data=Svc(id=service_id).pack()))
    return b.as_markup()


def confirm(service_id: int, ts: int, day: date) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="✅ Подтвердить", callback_data=Confirm(svc=service_id, ts=ts))
    b.button(text="◀️ Другое время", callback_data=Day(svc=service_id, day=day_to_int(day)))
    b.adjust(1)
    return b.as_markup()


def my_bookings(items: list[Booking], tz: ZoneInfo) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for bk in items:
        b.button(text=f"❌ {texts.fmt_dt(bk.starts_at, tz)}", callback_data=CancelBooking(id=bk.id))
    b.button(text="◀️ В меню", callback_data=Menu(action="home"))
    b.adjust(1)
    return b.as_markup()


# --- Admin keyboards ---


def admin_menu() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="📋 Записи на сегодня", callback_data=Admin(action="list", id=1))
    b.button(text="🗓 Записи на неделю", callback_data=Admin(action="list", id=7))
    b.button(text="💈 Услуги", callback_data=Admin(action="services"))
    b.button(text="🕘 Рабочие часы", callback_data=Admin(action="hours"))
    b.button(text="⭐ Предоплата", callback_data=Admin(action="deposit"))
    b.button(text="◀️ В меню", callback_data=Menu(action="home"))
    b.adjust(1)
    return b.as_markup()


def admin_back() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="◀️ Панель мастера", callback_data=Admin(action="menu"))
    return b.as_markup()


def admin_bookings(items: list[Booking], tz: ZoneInfo) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for bk in items[:30]:
        local = bk.starts_at.astimezone(tz)
        b.button(
            text=f"❌ {local:%d.%m %H:%M} {bk.user_name}",
            callback_data=Admin(action="cancel", id=bk.id),
        )
    b.button(text="◀️ Панель мастера", callback_data=Admin(action="menu"))
    b.adjust(1)
    return b.as_markup()


def admin_services(items: list[Service]) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for s in items:
        b.button(text=f"🗑 {s.name}", callback_data=Admin(action="svc_hide", id=s.id))
    b.button(text="➕ Добавить услугу", callback_data=Admin(action="svc_add"))
    b.button(text="◀️ Панель мастера", callback_data=Admin(action="menu"))
    b.adjust(1)
    return b.as_markup()


def admin_hours() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for wd in range(7):
        b.button(text=texts.WEEKDAYS_FULL[wd], callback_data=Admin(action="hours_edit", id=wd))
    b.adjust(2)
    b.row(InlineKeyboardButton(text="◀️ Панель мастера", callback_data=Admin(action="menu").pack()))

    return b.as_markup()

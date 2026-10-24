from datetime import date, datetime
from zoneinfo import ZoneInfo

from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from shared.i18n import LANGUAGE_BUTTON
from slotbook.models import Booking, Service
from slotbook.texts import Ru

# --- Callback data. Prefixes are short: Telegram limits callback data to 64 bytes ---


class Menu(CallbackData, prefix="m"):
    action: str  # home | book | my | lang


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


def main_menu(t: Ru, is_admin: bool) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text=t.BTN_BOOK, callback_data=Menu(action="book"))
    b.button(text=t.BTN_MY, callback_data=Menu(action="my"))
    if is_admin:
        b.button(text=t.BTN_ADMIN, callback_data=Admin(action="menu"))
    b.button(text=LANGUAGE_BUTTON, callback_data=Menu(action="lang"))
    b.adjust(1)
    return b.as_markup()


def back_home(t: Ru) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text=t.BTN_HOME, callback_data=Menu(action="home"))
    return b.as_markup()


def services(t: Ru, items: list[Service]) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for s in items:
        b.button(text=f"{s.name} · {s.price} {t.currency}", callback_data=Svc(id=s.id))
    b.button(text=t.BTN_HOME, callback_data=Menu(action="home"))
    b.adjust(1)
    return b.as_markup()


def days(t: Ru, service_id: int, items: list[date]) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for d in items:
        b.button(text=t.fmt_day(d), callback_data=Day(svc=service_id, day=day_to_int(d)))
    b.adjust(2)
    b.row(InlineKeyboardButton(text=t.BTN_SERVICES, callback_data=Menu(action="book").pack()))
    return b.as_markup()


def times(t: Ru, service_id: int, slots: list[datetime], tz: ZoneInfo) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for slot in slots:
        b.button(
            text=slot.astimezone(tz).strftime("%H:%M"),
            callback_data=Slot(svc=service_id, ts=int(slot.timestamp())),
        )
    b.adjust(4)
    b.row(InlineKeyboardButton(text=t.BTN_DAYS, callback_data=Svc(id=service_id).pack()))
    return b.as_markup()


def confirm(t: Ru, service_id: int, ts: int, day: date) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text=t.BTN_CONFIRM, callback_data=Confirm(svc=service_id, ts=ts))
    b.button(text=t.BTN_OTHER_TIME, callback_data=Day(svc=service_id, day=day_to_int(day)))
    b.adjust(1)
    return b.as_markup()


def my_bookings(t: Ru, items: list[Booking], tz: ZoneInfo) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for bk in items:
        b.button(text=f"❌ {t.fmt_dt(bk.starts_at, tz)}", callback_data=CancelBooking(id=bk.id))
    b.button(text=t.BTN_HOME, callback_data=Menu(action="home"))
    b.adjust(1)
    return b.as_markup()


# --- Admin keyboards ---


def admin_menu(t: Ru) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text=t.BTN_TODAY, callback_data=Admin(action="list", id=1))
    b.button(text=t.BTN_WEEK, callback_data=Admin(action="list", id=7))
    b.button(text=t.BTN_ADMIN_SERVICES, callback_data=Admin(action="services"))
    b.button(text=t.BTN_HOURS, callback_data=Admin(action="hours"))
    b.button(text=t.BTN_DEPOSIT, callback_data=Admin(action="deposit"))
    b.button(text=t.BTN_HOME, callback_data=Menu(action="home"))
    b.adjust(1)
    return b.as_markup()


def admin_back(t: Ru) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text=t.BTN_ADMIN_BACK, callback_data=Admin(action="menu"))
    return b.as_markup()


def admin_bookings(t: Ru, items: list[Booking], tz: ZoneInfo) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for bk in items[:30]:
        local = bk.starts_at.astimezone(tz)
        b.button(
            text=f"❌ {local:%d.%m %H:%M} {bk.user_name}",
            callback_data=Admin(action="cancel", id=bk.id),
        )
    b.button(text=t.BTN_ADMIN_BACK, callback_data=Admin(action="menu"))
    b.adjust(1)
    return b.as_markup()


def admin_services(t: Ru, items: list[Service]) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for s in items:
        b.button(text=f"🗑 {s.name}", callback_data=Admin(action="svc_hide", id=s.id))
    b.button(text=t.BTN_ADD_SERVICE, callback_data=Admin(action="svc_add"))
    b.button(text=t.BTN_ADMIN_BACK, callback_data=Admin(action="menu"))
    b.adjust(1)
    return b.as_markup()


def admin_hours(t: Ru) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for wd in range(7):
        b.button(text=t.WEEKDAYS_FULL[wd], callback_data=Admin(action="hours_edit", id=wd))
    b.adjust(2)
    b.row(InlineKeyboardButton(text=t.BTN_ADMIN_BACK, callback_data=Admin(action="menu").pack()))
    return b.as_markup()

"""Inline keyboards and their callback data."""

from datetime import UTC, date, datetime
from zoneinfo import ZoneInfo

from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from shared.i18n import LANGUAGE_BUTTON
from slotbook.models import Booking, BookingStatus, Service
from slotbook.texts import Ru, short

# Client names in the master's cancel buttons
BUTTON_NAME_LEN = 24

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
    """Asks first: cancelling may cost the client the deposit."""

    id: int


class CancelBookingYes(CallbackData, prefix="xy"):
    id: int


class Admin(CallbackData, prefix="a"):
    action: str
    id: int = 0


class AdminPage(CallbackData, prefix="ap"):
    """A page of the master's booking list (opened with Admin(action="list", id=days))."""

    days: int
    page: int


def day_to_int(d: date) -> int:
    return d.year * 10000 + d.month * 100 + d.day


def int_to_day(v: int) -> date | None:
    """YYYYMMDD -> date; None if it isn't a real date (callback data can be forged)."""
    try:
        return date(v // 10000, v // 100 % 100, v % 100)
    except (ValueError, OverflowError):
        return None


def ts_to_dt(ts: int) -> datetime | None:
    """Unix timestamp from callback data -> UTC datetime; None outside 1970-2106, which only
    forged data can have (and which would overflow date math later)."""
    if not 0 <= ts < 2**32:
        return None
    return datetime.fromtimestamp(ts, UTC)


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


def cancel_ask(t: Ru, booking_id: int) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text=t.BTN_CANCEL_YES, callback_data=CancelBookingYes(id=booking_id))
    b.button(text=t.BTN_KEEP, callback_data=Menu(action="my"))
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


def admin_bookings(
    t: Ru, items: list[Booking], tz: ZoneInfo, days: int, page: int, pages: int
) -> InlineKeyboardMarkup:
    """A cancel button for every booking on this page, then the page arrows."""
    b = InlineKeyboardBuilder()
    for bk in items:
        local = bk.starts_at.astimezone(tz)
        hold = " ⏳" if bk.status == BookingStatus.PENDING else ""
        b.button(
            text=f"❌ {local:%d.%m %H:%M}{hold} {short(bk.user_name, BUTTON_NAME_LEN)}",
            callback_data=Admin(action="cancel", id=bk.id),
        )
    b.adjust(1)
    arrows = []
    if page > 0:
        arrows.append(
            InlineKeyboardButton(text="◀️", callback_data=AdminPage(days=days, page=page - 1).pack())
        )
    if page < pages - 1:
        arrows.append(
            InlineKeyboardButton(text="▶️", callback_data=AdminPage(days=days, page=page + 1).pack())
        )
    if arrows:
        b.row(*arrows)
    b.row(InlineKeyboardButton(text=t.BTN_ADMIN_BACK, callback_data=Admin(action="menu").pack()))
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

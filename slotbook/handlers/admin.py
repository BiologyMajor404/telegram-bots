"""The master's panel: bookings, services, working hours, prepayment."""

import re
from datetime import datetime, time, timedelta
from html import escape
from zoneinfo import ZoneInfo

from aiogram import Bot, F, Router
from aiogram.filters import Command, Filter, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message, TelegramObject
from sqlalchemy.ext.asyncio import AsyncSession

from shared.formatting import user_link
from shared.notify import safe_send
from slotbook import keyboards as kb
from slotbook import payments, repo, scheduling
from slotbook.models import BookingStatus, WorkDay
from slotbook.texts import Ru


class IsAdmin(Filter):
    async def __call__(self, event: TelegramObject, admin_ids: set[int]) -> bool:
        user = getattr(event, "from_user", None)
        return user is not None and user.id in admin_ids


router = Router(name="admin")
router.message.filter(IsAdmin())
router.callback_query.filter(IsAdmin())


class AddService(StatesGroup):
    name = State()
    duration = State()
    price = State()


class EditHours(StatesGroup):
    value = State()


class EditDeposit(StatesGroup):
    value = State()


MAX_DEPOSIT_STARS = 10_000


HOURS_RE = re.compile(r"^(\d{1,2}):(\d{2})\s*-\s*(\d{1,2}):(\d{2})$")


def parse_hours(raw: str) -> tuple[time, time] | None:
    """'10:00-19:00' -> (10:00, 19:00); raises ValueError on bad input. '-' -> None (day off)."""
    raw = raw.strip()
    if raw == "-":
        return None
    m = HOURS_RE.match(raw)
    if not m:
        raise ValueError(raw)
    start = time(int(m[1]), int(m[2]))
    end = time(int(m[3]), int(m[4]))
    if start >= end:
        raise ValueError(raw)
    return start, end


def fmt_hours(t: Ru, wd: WorkDay | None) -> str:
    if wd is None or wd.start is None:
        return t.DAY_OFF
    return f"{wd.start:%H:%M}–{wd.end:%H:%M}"


# --- Menu ---


@router.message(Command("cancel"), StateFilter("*"))
async def cancel_action(message: Message, state: FSMContext, t: Ru) -> None:
    await state.clear()
    await message.answer(t.ACTION_CANCELLED, reply_markup=kb.admin_menu(t))


@router.message(Command("admin"))
async def admin_cmd(message: Message, state: FSMContext, t: Ru) -> None:
    await state.clear()
    await message.answer(t.ADMIN_MENU, reply_markup=kb.admin_menu(t))


@router.callback_query(kb.Admin.filter(F.action == "menu"))
async def admin_menu(cb: CallbackQuery, state: FSMContext, t: Ru) -> None:
    await state.clear()
    await cb.message.edit_text(t.ADMIN_MENU, reply_markup=kb.admin_menu(t))
    await cb.answer()


# --- Bookings ---


@router.callback_query(kb.Admin.filter(F.action == "list"))
async def list_bookings(
    cb: CallbackQuery, callback_data: kb.Admin, session: AsyncSession, tz: ZoneInfo, t: Ru
) -> None:
    today = scheduling.now_utc().astimezone(tz).date()
    start = datetime.combine(today, time(), tzinfo=tz)
    items = await repo.bookings_between(session, start, start + timedelta(days=callback_data.id))

    if not items:
        await cb.message.edit_text(t.ADMIN_NO_BOOKINGS, reply_markup=kb.admin_back(t))
        await cb.answer()
        return

    lines, current_day = [], None
    for b in items:
        local = b.starts_at.astimezone(tz)
        if local.date() != current_day:
            current_day = local.date()
            lines.append(f"\n<b>{t.fmt_day(current_day)}</b>")
        lines.append(
            f"{local:%H:%M}–{b.ends_at.astimezone(tz):%H:%M} · {escape(b.service.name)} · "
            f"{user_link(b.user_id, b.user_name)}"
        )
    await cb.message.edit_text(
        "\n".join(lines).strip(), reply_markup=kb.admin_bookings(t, items, tz)
    )
    await cb.answer()


@router.callback_query(kb.Admin.filter(F.action == "cancel"))
async def cancel_booking(
    cb: CallbackQuery,
    callback_data: kb.Admin,
    session: AsyncSession,
    tz: ZoneInfo,
    bot: Bot,
    t: Ru,
) -> None:
    booking = await repo.get_booking(session, callback_data.id)
    if not booking or booking.status != BookingStatus.ACTIVE:
        await cb.answer(t.CANT_CANCEL, show_alert=True)
        return
    give_back = payments.refund_due(booking, scheduling.now_utc(), by_master=True)
    await repo.cancel_booking(session, booking)
    refunded = give_back and await payments.refund(bot, session, booking)
    client_t = await repo.texts_for(session, booking.user_id)
    await safe_send(
        bot,
        booking.user_id,
        client_t.CLIENT_CANCELLED_BY_ADMIN.format(booking=client_t.fmt_booking(booking, tz))
        + (client_t.DEPOSIT_RETURNED if refunded else ""),
    )
    await cb.message.edit_text(t.ADMIN_CANCELLED, reply_markup=kb.admin_back(t))
    await cb.answer()


# --- Services ---


async def show_services(cb: CallbackQuery, session: AsyncSession, t: Ru) -> None:
    services = await repo.active_services(session)
    listing = "\n".join(t.fmt_service(s) for s in services) or "—"
    await cb.message.edit_text(
        t.ADMIN_SERVICES.format(items=listing), reply_markup=kb.admin_services(t, services)
    )


@router.callback_query(kb.Admin.filter(F.action == "services"))
async def services(cb: CallbackQuery, session: AsyncSession, t: Ru) -> None:
    await show_services(cb, session, t)
    await cb.answer()


@router.callback_query(kb.Admin.filter(F.action == "svc_hide"))
async def hide_service(
    cb: CallbackQuery, callback_data: kb.Admin, session: AsyncSession, t: Ru
) -> None:
    await repo.hide_service(session, callback_data.id)
    await show_services(cb, session, t)
    await cb.answer()


@router.callback_query(kb.Admin.filter(F.action == "svc_add"))
async def add_service_start(cb: CallbackQuery, state: FSMContext, t: Ru) -> None:
    await state.set_state(AddService.name)
    await cb.message.answer(t.ADMIN_ASK_NAME)
    await cb.answer()


@router.message(AddService.name, F.text)
async def add_service_name(message: Message, state: FSMContext, t: Ru) -> None:
    await state.update_data(name=message.text.strip()[:64])
    await state.set_state(AddService.duration)
    await message.answer(t.ADMIN_ASK_DURATION)


@router.message(AddService.duration, F.text)
async def add_service_duration(message: Message, state: FSMContext, t: Ru) -> None:
    if not message.text.isdigit() or int(message.text) <= 0:
        await message.answer(t.ADMIN_BAD_NUMBER)
        return
    if int(message.text) % 30:
        await message.answer(t.ADMIN_BAD_DURATION)
        return
    await state.update_data(duration=int(message.text))
    await state.set_state(AddService.price)
    await message.answer(t.ADMIN_ASK_PRICE)


@router.message(AddService.price, F.text)
async def add_service_price(
    message: Message, state: FSMContext, session: AsyncSession, t: Ru
) -> None:
    if not message.text.isdigit():
        await message.answer(t.ADMIN_BAD_NUMBER)
        return
    data = await state.get_data()
    await repo.add_service(session, data["name"], data["duration"], int(message.text))
    await state.clear()
    await message.answer(t.ADMIN_SERVICE_ADDED, reply_markup=kb.admin_menu(t))


# --- Working hours ---


@router.callback_query(kb.Admin.filter(F.action == "hours"))
async def hours(cb: CallbackQuery, session: AsyncSession, t: Ru) -> None:
    days = await repo.work_days(session)
    listing = "\n".join(f"{t.WEEKDAYS_FULL[wd]}: {fmt_hours(t, days.get(wd))}" for wd in range(7))
    await cb.message.edit_text(t.ADMIN_HOURS.format(items=listing), reply_markup=kb.admin_hours(t))
    await cb.answer()


@router.callback_query(kb.Admin.filter(F.action == "hours_edit"))
async def hours_edit_start(
    cb: CallbackQuery, callback_data: kb.Admin, state: FSMContext, t: Ru
) -> None:
    await state.set_state(EditHours.value)
    await state.update_data(weekday=callback_data.id)
    await cb.message.answer(t.ADMIN_ASK_HOURS.format(day=t.WEEKDAYS_FULL[callback_data.id]))
    await cb.answer()


@router.message(EditHours.value, F.text)
async def hours_edit_save(
    message: Message, state: FSMContext, session: AsyncSession, t: Ru
) -> None:
    try:
        parsed = parse_hours(message.text)
    except ValueError:
        await message.answer(t.ADMIN_BAD_HOURS)
        return
    weekday = (await state.get_data())["weekday"]
    start, end = parsed if parsed else (None, None)
    await repo.set_work_day(session, weekday, start, end)
    await state.clear()
    await message.answer(t.ADMIN_HOURS_SAVED, reply_markup=kb.admin_menu(t))


# --- Deposit ---


@router.callback_query(kb.Admin.filter(F.action == "deposit"))
async def deposit_start(cb: CallbackQuery, state: FSMContext, session: AsyncSession, t: Ru) -> None:
    stars = await repo.get_deposit(session)
    current = f"{stars} ⭐" if stars else t.ADMIN_DEPOSIT_OFF_LABEL
    await state.set_state(EditDeposit.value)
    await cb.message.answer(t.ADMIN_ASK_DEPOSIT.format(current=current))
    await cb.answer()


@router.message(EditDeposit.value, F.text)
async def deposit_save(message: Message, state: FSMContext, session: AsyncSession, t: Ru) -> None:
    raw = message.text.strip()
    if not raw.isdigit() or int(raw) > MAX_DEPOSIT_STARS:
        await message.answer(t.ADMIN_BAD_DEPOSIT.format(max=MAX_DEPOSIT_STARS))
        return
    await repo.set_deposit(session, int(raw))
    await state.clear()
    text = t.ADMIN_DEPOSIT_ON.format(stars=raw) if int(raw) else t.ADMIN_DEPOSIT_OFF
    await message.answer(text, reply_markup=kb.admin_menu(t))

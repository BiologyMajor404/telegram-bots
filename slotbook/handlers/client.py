from datetime import UTC, date, datetime
from html import escape
from zoneinfo import ZoneInfo

from aiogram import Bot, F, Router
from aiogram.filters import CommandStart
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from shared.notify import notify_all
from slotbook import keyboards as kb
from slotbook import payments, repo, scheduling, texts
from slotbook.models import BookingStatus, Service

router = Router(name="client")


@router.message(CommandStart())
async def start(message: Message, admin_ids: set[int]) -> None:
    await message.answer(
        texts.WELCOME.format(name=escape(message.from_user.first_name)),
        reply_markup=kb.main_menu(message.from_user.id in admin_ids),
    )


@router.callback_query(kb.Menu.filter(F.action == "home"))
async def home(cb: CallbackQuery, admin_ids: set[int]) -> None:
    await cb.message.edit_text(
        texts.MAIN_MENU, reply_markup=kb.main_menu(cb.from_user.id in admin_ids)
    )
    await cb.answer()


@router.callback_query(kb.Menu.filter(F.action == "book"))
async def choose_service(cb: CallbackQuery, session: AsyncSession) -> None:
    services = await repo.active_services(session)
    if not services:
        await cb.answer(texts.NO_SERVICES, show_alert=True)
        return
    await cb.message.edit_text(texts.CHOOSE_SERVICE, reply_markup=kb.services(services))
    await cb.answer()


@router.callback_query(kb.Svc.filter())
async def choose_day(
    cb: CallbackQuery, callback_data: kb.Svc, session: AsyncSession, tz: ZoneInfo
) -> None:
    service = await repo.get_service(session, callback_data.id)
    if not service or not service.is_active:
        await cb.answer(texts.NO_SERVICES, show_alert=True)
        return
    days = await scheduling.free_days(session, service, tz)
    if not days:
        await cb.answer(texts.NO_DAYS, show_alert=True)
        return
    await cb.message.edit_text(
        texts.CHOOSE_DAY.format(service=texts.fmt_service(service)),
        reply_markup=kb.days(service.id, days),
    )
    await cb.answer()


async def choose_time_text(session: AsyncSession, service: Service, day: date) -> str:
    # Explains why late slots are missing: the service must end before closing time
    wd = (await repo.work_days(session))[day.weekday()]
    return texts.CHOOSE_TIME.format(
        service=texts.fmt_service(service),
        day=texts.fmt_day(day),
        duration=service.duration_min,
        end=f"{wd.end:%H:%M}",
    )


@router.callback_query(kb.Day.filter())
async def choose_time(
    cb: CallbackQuery, callback_data: kb.Day, session: AsyncSession, tz: ZoneInfo
) -> None:
    service = await repo.get_service(session, callback_data.svc)
    if not service or not service.is_active:
        await cb.answer(texts.NO_SERVICES, show_alert=True)
        return
    day = kb.int_to_day(callback_data.day)
    slots = await scheduling.free_slots(session, service, tz, day)
    if not slots:
        await cb.answer(texts.NO_TIME, show_alert=True)
        return
    await cb.message.edit_text(
        await choose_time_text(session, service, day),
        reply_markup=kb.times(service.id, slots, tz),
    )
    await cb.answer()


@router.callback_query(kb.Slot.filter())
async def confirm(
    cb: CallbackQuery, callback_data: kb.Slot, session: AsyncSession, tz: ZoneInfo
) -> None:
    service = await repo.get_service(session, callback_data.svc)
    if not service or not service.is_active:
        await cb.answer(texts.NO_SERVICES, show_alert=True)
        return
    starts_at = datetime.fromtimestamp(callback_data.ts, UTC)
    await cb.message.edit_text(
        texts.CONFIRM.format(dt=texts.fmt_dt(starts_at, tz), service=texts.fmt_service(service)),
        reply_markup=kb.confirm(service.id, callback_data.ts, starts_at.astimezone(tz).date()),
    )
    await cb.answer()


@router.callback_query(kb.Confirm.filter())
async def create_booking(
    cb: CallbackQuery,
    callback_data: kb.Confirm,
    session: AsyncSession,
    tz: ZoneInfo,
    bot: Bot,
    admin_ids: set[int],
) -> None:
    service = await repo.get_service(session, callback_data.svc)
    if not service or not service.is_active:
        await cb.answer(texts.NO_SERVICES, show_alert=True)
        return
    starts_at = datetime.fromtimestamp(callback_data.ts, UTC)
    deposit = await repo.get_deposit(session)
    booking = await scheduling.book(session, service, starts_at, cb.from_user, tz, deposit)
    if booking is None:
        await cb.answer(texts.SLOT_TAKEN, show_alert=True)
        day = starts_at.astimezone(tz).date()
        slots = await scheduling.free_slots(session, service, tz, day)
        if slots:
            await cb.message.edit_text(
                await choose_time_text(session, service, day),
                reply_markup=kb.times(service.id, slots, tz),
            )
        else:
            await cb.message.edit_text(texts.NO_TIME, reply_markup=kb.back_home())
        return

    if booking.status == BookingStatus.PENDING:
        # The booking is confirmed (and the master notified) after the deposit is paid
        await cb.message.edit_text(
            texts.PAY_REQUIRED.format(
                booking=texts.fmt_booking(booking, tz),
                stars=booking.deposit_stars,
                minutes=int(payments.HOLD_TIME.total_seconds() // 60),
                hours=int(payments.FREE_CANCEL_BEFORE.total_seconds() // 3600),
            ),
            reply_markup=kb.back_home(),
        )
        await cb.answer()
        await payments.send_invoice(bot, booking, tz)
        return

    await cb.message.edit_text(
        texts.BOOKED.format(booking=texts.fmt_booking(booking, tz)), reply_markup=kb.back_home()
    )
    await cb.answer()
    await notify_all(
        bot,
        admin_ids,
        texts.ADMIN_NEW.format(
            booking=texts.fmt_booking(booking, tz),
            client=texts.user_link(booking.user_id, booking.user_name),
        ),
    )


async def show_my_bookings(cb: CallbackQuery, session: AsyncSession, tz: ZoneInfo) -> None:
    items = await repo.upcoming_user_bookings(session, cb.from_user.id, scheduling.now_utc())
    if not items:
        await cb.message.edit_text(texts.MY_EMPTY, reply_markup=kb.back_home())
        return
    listing = "\n\n".join(texts.fmt_booking(b, tz) for b in items)
    await cb.message.edit_text(
        texts.MY_LIST.format(items=listing), reply_markup=kb.my_bookings(items, tz)
    )


@router.callback_query(kb.Menu.filter(F.action == "my"))
async def my_bookings(cb: CallbackQuery, session: AsyncSession, tz: ZoneInfo) -> None:
    await show_my_bookings(cb, session, tz)
    await cb.answer()


@router.callback_query(kb.CancelBooking.filter())
async def cancel_booking(
    cb: CallbackQuery,
    callback_data: kb.CancelBooking,
    session: AsyncSession,
    tz: ZoneInfo,
    bot: Bot,
    admin_ids: set[int],
) -> None:
    booking = await repo.get_booking(session, callback_data.id)
    if (
        not booking
        or booking.user_id != cb.from_user.id
        or booking.status != BookingStatus.ACTIVE
        or booking.starts_at <= scheduling.now_utc()
    ):
        await cb.answer(texts.CANT_CANCEL, show_alert=True)
        return
    paid = payments.is_paid(booking)
    give_back = payments.refund_due(booking, scheduling.now_utc(), by_master=False)
    await repo.cancel_booking(session, booking)
    if give_back and await payments.refund(bot, session, booking):
        await cb.answer(texts.CANCELLED_REFUNDED, show_alert=True)
    elif paid:
        await cb.answer(texts.CANCELLED_NO_REFUND, show_alert=True)
    else:
        await cb.answer(texts.CANCELLED)
    await show_my_bookings(cb, session, tz)
    await notify_all(
        bot,
        admin_ids,
        texts.ADMIN_CANCELLED_BY_CLIENT.format(
            booking=texts.fmt_booking(booking, tz),
            client=texts.user_link(booking.user_id, booking.user_name),
        ),
    )


@router.message()
async def fallback(message: Message, admin_ids: set[int]) -> None:
    await message.answer(
        texts.UNKNOWN, reply_markup=kb.main_menu(message.from_user.id in admin_ids)
    )

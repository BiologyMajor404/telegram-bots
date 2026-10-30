"""The client side: booking a slot, my bookings, cancelling, language."""

from datetime import date, datetime
from html import escape
from zoneinfo import ZoneInfo

from aiogram import Bot, F, Router
from aiogram.enums import ChatType
from aiogram.filters import Command, CommandStart
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from shared.formatting import user_link
from shared.i18n import CHOOSE_LANGUAGE, SetLang, lang_keyboard
from slotbook import keyboards as kb
from slotbook import payments, repo, scheduling
from slotbook.i18n import notify_admins
from slotbook.models import Booking, BookingStatus, Service
from slotbook.texts import TEXTS, Ru

router = Router(name="client")
# Booking is personal: in a group the menus would be shared with everyone, and an invoice
# can't reach someone who never opened the bot
router.message.filter(F.chat.type == ChatType.PRIVATE)
router.callback_query.filter(F.message.chat.type == ChatType.PRIVATE)


@router.message(CommandStart())
async def start(message: Message, admin_ids: set[int], t: Ru) -> None:
    await message.answer(
        t.WELCOME.format(name=escape(message.from_user.first_name)),
        reply_markup=kb.main_menu(t, message.from_user.id in admin_ids),
    )


@router.callback_query(kb.Menu.filter(F.action == "home"))
async def home(cb: CallbackQuery, admin_ids: set[int], t: Ru) -> None:
    await cb.message.edit_text(
        t.MAIN_MENU, reply_markup=kb.main_menu(t, cb.from_user.id in admin_ids)
    )
    await cb.answer()


# --- Language ---


@router.message(Command("language"))
async def language_cmd(message: Message) -> None:
    await message.answer(CHOOSE_LANGUAGE, reply_markup=lang_keyboard())


@router.callback_query(kb.Menu.filter(F.action == "lang"))
async def language_menu(cb: CallbackQuery) -> None:
    await cb.message.edit_text(CHOOSE_LANGUAGE, reply_markup=lang_keyboard())
    await cb.answer()


@router.callback_query(SetLang.filter())
async def set_language(
    cb: CallbackQuery, callback_data: SetLang, session: AsyncSession, admin_ids: set[int]
) -> None:
    t = TEXTS.get(callback_data.code)
    if t is None:
        await cb.answer()
        return
    await repo.set_lang(session, cb.from_user.id, t.LANG)
    await cb.message.edit_text(
        t.LANGUAGE_SET, reply_markup=kb.main_menu(t, cb.from_user.id in admin_ids)
    )
    await cb.answer()


# --- Booking ---


@router.callback_query(kb.Menu.filter(F.action == "book"))
async def choose_service(cb: CallbackQuery, session: AsyncSession, t: Ru) -> None:
    services = await repo.active_services(session)
    if not services:
        await cb.answer(t.NO_SERVICES, show_alert=True)
        return
    await cb.message.edit_text(t.CHOOSE_SERVICE, reply_markup=kb.services(t, services))
    await cb.answer()


@router.callback_query(kb.Svc.filter())
async def choose_day(
    cb: CallbackQuery, callback_data: kb.Svc, session: AsyncSession, tz: ZoneInfo, t: Ru
) -> None:
    service = await repo.get_service(session, callback_data.id)
    if not service or not service.is_active:
        await cb.answer(t.NO_SERVICES, show_alert=True)
        return
    days = await scheduling.free_days(session, service, tz)
    if not days:
        await cb.answer(t.NO_DAYS, show_alert=True)
        return
    await cb.message.edit_text(
        t.CHOOSE_DAY.format(service=t.fmt_service(service)),
        reply_markup=kb.days(t, service.id, days),
    )
    await cb.answer()


async def choose_time_text(t: Ru, session: AsyncSession, service: Service, day: date) -> str:
    # Explains why late slots are missing: the service must end before closing time
    wd = (await repo.work_days(session))[day.weekday()]
    return t.CHOOSE_TIME.format(
        service=t.fmt_service(service),
        day=t.fmt_day(day),
        duration=service.duration_min,
        end=f"{wd.end:%H:%M}",
    )


def slot_from(ts: int, tz: ZoneInfo) -> datetime | None:
    """The slot start from callback data, if it's on a day that can be booked."""
    starts_at = kb.ts_to_dt(ts)
    if starts_at is None or not scheduling.bookable_day(starts_at.astimezone(tz).date(), tz):
        return None
    return starts_at


@router.callback_query(kb.Day.filter())
async def choose_time(
    cb: CallbackQuery, callback_data: kb.Day, session: AsyncSession, tz: ZoneInfo, t: Ru
) -> None:
    service = await repo.get_service(session, callback_data.svc)
    if not service or not service.is_active:
        await cb.answer(t.NO_SERVICES, show_alert=True)
        return
    day = kb.int_to_day(callback_data.day)
    if day is None or not scheduling.bookable_day(day, tz):
        await cb.answer(t.NO_TIME, show_alert=True)
        return
    slots = await scheduling.free_slots(session, service, tz, day)
    if not slots:
        await cb.answer(t.NO_TIME, show_alert=True)
        return
    await cb.message.edit_text(
        await choose_time_text(t, session, service, day),
        reply_markup=kb.times(t, service.id, slots, tz),
    )
    await cb.answer()


@router.callback_query(kb.Slot.filter())
async def confirm(
    cb: CallbackQuery, callback_data: kb.Slot, session: AsyncSession, tz: ZoneInfo, t: Ru
) -> None:
    service = await repo.get_service(session, callback_data.svc)
    if not service or not service.is_active:
        await cb.answer(t.NO_SERVICES, show_alert=True)
        return
    starts_at = slot_from(callback_data.ts, tz)
    if starts_at is None:
        await cb.answer(t.NO_TIME, show_alert=True)
        return
    await cb.message.edit_text(
        t.CONFIRM.format(dt=t.fmt_dt(starts_at, tz), service=t.fmt_service(service)),
        reply_markup=kb.confirm(t, service.id, callback_data.ts, starts_at.astimezone(tz).date()),
    )
    await cb.answer()


def refusal_text(t: Ru, e: scheduling.CantBookError) -> str | None:
    """What to tell a client whose booking book() turned down. None for a second tap on
    Confirm: the first tap is already showing the booking."""
    if isinstance(e, scheduling.BookingLimitError):
        return t.TOO_MANY_BOOKINGS.format(limit=scheduling.MAX_OPEN_BOOKINGS)
    if isinstance(e, scheduling.HoldExistsError):
        return t.HOLD_EXISTS
    if isinstance(e, scheduling.RebookCooldownError):
        return t.REBOOK_COOLDOWN.format(minutes=e.minutes)
    return None


async def show_other_times(
    cb: CallbackQuery,
    session: AsyncSession,
    service: Service,
    starts_at: datetime,
    tz: ZoneInfo,
    t: Ru,
) -> None:
    """After the slot was taken: the free times left that day. book() ended its transaction
    with a commit, so `service` is still loaded."""
    day = starts_at.astimezone(tz).date()
    slots = await scheduling.free_slots(session, service, tz, day)
    if slots:
        await cb.message.edit_text(
            await choose_time_text(t, session, service, day),
            reply_markup=kb.times(t, service.id, slots, tz),
        )
    else:
        await cb.message.edit_text(t.NO_TIME, reply_markup=kb.back_home(t))


@router.callback_query(kb.Confirm.filter())
async def create_booking(
    cb: CallbackQuery,
    callback_data: kb.Confirm,
    session: AsyncSession,
    tz: ZoneInfo,
    bot: Bot,
    admin_ids: set[int],
    t: Ru,
) -> None:
    service = await repo.get_service(session, callback_data.svc)
    if not service or not service.is_active:
        await cb.answer(t.NO_SERVICES, show_alert=True)
        return
    starts_at = slot_from(callback_data.ts, tz)
    if starts_at is None:
        await cb.answer(t.NO_TIME, show_alert=True)
        return
    deposit = await repo.get_deposit(session)
    try:
        booking = await scheduling.book(session, service, starts_at, cb.from_user, tz, deposit)
    except scheduling.CantBookError as e:
        text = refusal_text(t, e)
        await cb.answer(text, show_alert=text is not None)
        return
    if booking is None:
        await cb.answer(t.SLOT_TAKEN, show_alert=True)
        await show_other_times(cb, session, service, starts_at, tz, t)
        return

    if booking.status == BookingStatus.PENDING:
        # The booking is confirmed (and the master notified) after the deposit is paid
        await cb.message.edit_text(
            t.PAY_REQUIRED.format(
                booking=t.fmt_booking(booking, tz),
                stars=booking.deposit_stars,
                minutes=int(payments.HOLD_TIME.total_seconds() // 60),
                hours=int(payments.FREE_CANCEL_BEFORE.total_seconds() // 3600),
            ),
            reply_markup=kb.back_home(t),
        )
        await cb.answer()
        await payments.send_invoice(bot, booking, tz, t)
        return

    await cb.message.edit_text(
        t.BOOKED.format(booking=t.fmt_booking(booking, tz)), reply_markup=kb.back_home(t)
    )
    await cb.answer()
    await notify_admins(
        bot,
        session,
        admin_ids,
        lambda at: at.ADMIN_NEW.format(
            booking=at.fmt_booking(booking, tz),
            client=user_link(booking.user_id, booking.user_name),
        ),
    )


# --- My bookings ---


async def show_my_bookings(cb: CallbackQuery, session: AsyncSession, tz: ZoneInfo, t: Ru) -> None:
    items = await repo.upcoming_user_bookings(session, cb.from_user.id, scheduling.now_utc())
    if not items:
        await cb.message.edit_text(t.MY_EMPTY, reply_markup=kb.back_home(t))
        return
    listing = "\n\n".join(t.fmt_booking(b, tz) for b in items)
    await cb.message.edit_text(
        t.MY_LIST.format(items=listing), reply_markup=kb.my_bookings(t, items, tz)
    )


@router.callback_query(kb.Menu.filter(F.action == "my"))
async def my_bookings(cb: CallbackQuery, session: AsyncSession, tz: ZoneInfo, t: Ru) -> None:
    await show_my_bookings(cb, session, tz, t)
    await cb.answer()


async def own_open_booking(session: AsyncSession, booking_id: int, user_id: int) -> Booking | None:
    """The client's own upcoming booking (or hold waiting for the deposit) to cancel."""
    booking = await repo.get_booking(session, booking_id)
    if (
        booking is None
        or booking.user_id != user_id
        or booking.status not in BookingStatus.OPEN
        or booking.starts_at <= scheduling.now_utc()
    ):
        return None
    return booking


def deposit_note(t: Ru, booking: Booking, now: datetime) -> str:
    """What happens to a paid deposit if the client cancels now."""
    if not payments.is_paid(booking):
        return ""
    if payments.refund_due(booking, now, by_master=False):
        return t.CANCEL_ASK_REFUND.format(stars=booking.deposit_stars)
    return t.CANCEL_ASK_NO_REFUND.format(stars=booking.deposit_stars)


@router.callback_query(kb.CancelBooking.filter())
async def cancel_ask(
    cb: CallbackQuery, callback_data: kb.CancelBooking, session: AsyncSession, tz: ZoneInfo, t: Ru
) -> None:
    booking = await own_open_booking(session, callback_data.id, cb.from_user.id)
    if booking is None:
        await cb.answer(t.CANT_CANCEL, show_alert=True)
        return
    await cb.message.edit_text(
        t.CANCEL_ASK.format(booking=t.fmt_booking(booking, tz))
        + deposit_note(t, booking, scheduling.now_utc()),
        reply_markup=kb.cancel_ask(t, booking.id),
    )
    await cb.answer()


@router.callback_query(kb.CancelBookingYes.filter())
async def cancel_booking(
    cb: CallbackQuery,
    callback_data: kb.CancelBookingYes,
    session: AsyncSession,
    tz: ZoneInfo,
    bot: Bot,
    admin_ids: set[int],
    t: Ru,
) -> None:
    booking = await own_open_booking(session, callback_data.id, cb.from_user.id)
    if booking is None:
        await cb.answer(t.CANT_CANCEL, show_alert=True)
        return
    now = scheduling.now_utc()
    was_active = booking.status == BookingStatus.ACTIVE
    paid = payments.is_paid(booking)
    give_back = payments.refund_due(booking, now, by_master=False)
    cooldown = scheduling.cancel_starts_cooldown(booking, now)
    # Fails if a double tap, a payment or the expiry job changed the booking meanwhile
    if not await repo.cancel_booking(session, booking, refund=give_back):
        await cb.answer(t.CANT_CANCEL, show_alert=True)
        return
    if cooldown:
        scheduling.start_cooldown(cb.from_user.id, now)

    refunded = give_back and await payments.refund(bot, session, booking)
    if refunded:
        await cb.answer(t.CANCELLED_REFUNDED, show_alert=True)
    elif give_back:
        await cb.answer(t.CANCELLED_REFUND_PENDING, show_alert=True)
    elif paid:
        await cb.answer(t.CANCELLED_NO_REFUND, show_alert=True)
    else:
        await cb.answer(t.CANCELLED)
    await show_my_bookings(cb, session, tz, t)
    if was_active:  # the master never heard of a hold that wasn't paid
        await notify_admins(
            bot,
            session,
            admin_ids,
            lambda at: at.ADMIN_CANCELLED_BY_CLIENT.format(
                booking=at.fmt_booking(booking, tz),
                client=user_link(booking.user_id, booking.user_name),
            ),
        )
    if give_back and not refunded:
        await payments.alert_refund_failed(bot, session, booking, admin_ids, tz)


# Text only: service messages (a refund notice, say) need no "didn't get that"
@router.message(F.text)
async def fallback(message: Message, admin_ids: set[int], t: Ru) -> None:
    await message.answer(t.UNKNOWN, reply_markup=kb.main_menu(t, message.from_user.id in admin_ids))

"""Telegram Stars deposit: pre-checkout check, payment, /paysupport."""

import logging
from html import escape
from zoneinfo import ZoneInfo

from aiogram import Bot, F, Router
from aiogram.filters import Command
from aiogram.types import Message, PreCheckoutQuery
from sqlalchemy.ext.asyncio import AsyncSession

from shared.formatting import user_link
from slotbook import keyboards as kb
from slotbook import payments, repo
from slotbook.i18n import notify_admins
from slotbook.models import Booking, BookingStatus
from slotbook.texts import Ru

log = logging.getLogger(__name__)
router = Router(name="payments")


@router.pre_checkout_query()
async def pre_checkout(query: PreCheckoutQuery, session: AsyncSession, t: Ru) -> None:
    """Last check before Telegram charges the client: the hold must still be valid."""
    booking_id = payments.parse_payload(query.invoice_payload)
    booking = await repo.get_booking(session, booking_id) if booking_id else None
    valid = (
        booking is not None
        and booking.status == BookingStatus.PENDING
        and booking.user_id == query.from_user.id
        and query.total_amount == booking.deposit_stars
    )
    if valid:
        await query.answer(ok=True)
    else:
        await query.answer(ok=False, error_message=t.PAY_EXPIRED)


@router.message(F.successful_payment)
async def successful_payment(
    message: Message,
    session: AsyncSession,
    tz: ZoneInfo,
    bot: Bot,
    admin_ids: set[int],
    t: Ru,
) -> None:
    payment = message.successful_payment
    charge = payment.telegram_payment_charge_id
    booking_id = payments.parse_payload(payment.invoice_payload)
    booking = await repo.get_booking(session, booking_id) if booking_id else None
    if booking is None:
        log.error("Payment %s for unknown booking", charge)
        return

    if await repo.activate_paid(session, booking, charge):
        await message.answer(
            t.BOOKED.format(booking=t.fmt_booking(booking, tz)), reply_markup=kb.back_home(t)
        )
        await notify_admins(
            bot,
            session,
            admin_ids,
            lambda at: at.ADMIN_NEW.format(
                booking=at.fmt_booking(booking, tz),
                client=user_link(booking.user_id, booking.user_name),
            ),
        )
        return

    # The booking no longer waits for payment. Each step below is atomic and leaves `booking`
    # reloaded, so a copy of this update handled at the same moment can't count it twice
    if await repo.record_late_payment(session, booking, charge):
        # The hold was released before the money came: give it back, retried if this fails
        refunded = await payments.refund(bot, session, booking)
        text = t.PAY_LATE_REFUNDED if refunded else t.PAY_LATE_REFUND_PENDING
        await message.answer(text, reply_markup=kb.back_home(t))
        if not refunded:
            await payments.alert_refund_failed(bot, session, booking, admin_ids, tz)
    elif booking.payment_charge_id == charge:
        log.info("Payment %s was already handled", charge)  # the update came again
    else:
        await refund_extra(message, session, bot, booking, charge, admin_ids, tz, t)


async def refund_extra(
    message: Message,
    session: AsyncSession,
    bot: Bot,
    booking: Booking,
    charge: str,
    admin_ids: set[int],
    tz: ZoneInfo,
    t: Ru,
) -> None:
    """A second payment for an already paid booking (two copies of the invoice paid at once):
    give it back and keep the stored payment, which is the one a cancellation refunds."""
    stars = message.successful_payment.total_amount
    if await payments.refund_charge(bot, booking.user_id, charge):
        await message.answer(t.PAY_EXTRA_REFUNDED, reply_markup=kb.back_home(t))
        return
    await message.answer(t.PAY_EXTRA_REFUND_FAILED, reply_markup=kb.back_home(t))
    # Not stored anywhere for a retry: the admins get what's needed to refund it by hand
    await notify_admins(
        bot,
        session,
        admin_ids,
        lambda at: at.ADMIN_EXTRA_REFUND_FAILED.format(
            client=user_link(booking.user_id, booking.user_name),
            stars=stars,
            booking=at.fmt_booking(booking, tz),
            charge=escape(charge),
        ),
    )


@router.message(Command("paysupport"))
async def paysupport(message: Message, t: Ru, support_contact: str) -> None:
    # Telegram requires bots that accept Stars to answer /paysupport
    text = t.PAYSUPPORT
    if support_contact:
        text += t.PAYSUPPORT_CONTACT.format(contact=escape(support_contact))
    await message.answer(text)

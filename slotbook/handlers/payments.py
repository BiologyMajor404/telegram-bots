import logging
from zoneinfo import ZoneInfo

from aiogram import Bot, F, Router
from aiogram.filters import Command
from aiogram.types import Message, PreCheckoutQuery
from sqlalchemy.ext.asyncio import AsyncSession

from shared.notify import notify_all
from slotbook import keyboards as kb
from slotbook import payments, repo, texts
from slotbook.models import BookingStatus

log = logging.getLogger(__name__)
router = Router(name="payments")


@router.pre_checkout_query()
async def pre_checkout(query: PreCheckoutQuery, session: AsyncSession) -> None:
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
        await query.answer(ok=False, error_message=texts.PAY_EXPIRED)


@router.message(F.successful_payment)
async def successful_payment(
    message: Message, session: AsyncSession, tz: ZoneInfo, bot: Bot, admin_ids: set[int]
) -> None:
    payment = message.successful_payment
    booking_id = payments.parse_payload(payment.invoice_payload)
    booking = await repo.get_booking(session, booking_id) if booking_id else None
    if booking is None:
        log.error("Payment %s for unknown booking", payment.telegram_payment_charge_id)
        return

    if booking.status != BookingStatus.PENDING:
        # The hold expired between the pre-checkout check and the payment: give the money back
        booking.payment_charge_id = payment.telegram_payment_charge_id
        await session.commit()
        await payments.refund(bot, session, booking)
        await message.answer(texts.PAY_LATE_REFUNDED, reply_markup=kb.back_home())
        return

    await repo.mark_paid(session, booking, payment.telegram_payment_charge_id)
    await message.answer(
        texts.BOOKED.format(booking=texts.fmt_booking(booking, tz)), reply_markup=kb.back_home()
    )
    await notify_all(
        bot,
        admin_ids,
        texts.ADMIN_NEW.format(
            booking=texts.fmt_booking(booking, tz),
            client=texts.user_link(booking.user_id, booking.user_name),
        ),
    )


@router.message(Command("paysupport"))
async def paysupport(message: Message) -> None:
    # Telegram requires bots that accept Stars to answer /paysupport
    await message.answer(texts.PAYSUPPORT)

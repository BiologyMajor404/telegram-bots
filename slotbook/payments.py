"""Deposit in Telegram Stars: invoice, refund policy and refunds."""

import logging
from collections.abc import Iterable
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError
from aiogram.types import LabeledPrice
from sqlalchemy.ext.asyncio import AsyncSession

from shared.formatting import user_link
from slotbook.i18n import notify_admins
from slotbook.models import Booking
from slotbook.texts import Ru

log = logging.getLogger(__name__)

STARS = "XTR"  # Telegram Stars currency code; no payment provider token needed
# How long a slot is held while the client pays the deposit
HOLD_TIME = timedelta(minutes=15)
# Cancelling earlier than this before the visit returns the deposit
FREE_CANCEL_BEFORE = timedelta(hours=24)
PAYLOAD_PREFIX = "booking:"
# Telegram's error for a payment that was already given back (e.g. by an earlier try whose
# answer got lost): the money is back, so it counts as done
ALREADY_REFUNDED = "CHARGE_ALREADY_REFUNDED"


def invoice_payload(booking_id: int) -> str:
    return f"{PAYLOAD_PREFIX}{booking_id}"


def parse_payload(payload: str) -> int | None:
    if not payload.startswith(PAYLOAD_PREFIX):
        return None
    tail = payload.removeprefix(PAYLOAD_PREFIX)
    return int(tail) if tail.isdigit() else None


def is_paid(booking: Booking) -> bool:
    return bool(booking.payment_charge_id) and not booking.refunded


def refund_due(booking: Booking, now: datetime, by_master: bool) -> bool:
    """The master cancelling always refunds; the client gets money back only if
    cancelling early enough."""
    if not is_paid(booking):
        return False
    return by_master or booking.starts_at - now >= FREE_CANCEL_BEFORE


async def send_invoice(bot: Bot, booking: Booking, tz: ZoneInfo, t: Ru) -> None:
    await bot.send_invoice(
        chat_id=booking.user_id,
        title=t.INVOICE_TITLE,
        description=t.INVOICE_DESCRIPTION.format(
            service=booking.service.name, dt=t.fmt_dt(booking.starts_at, tz)
        ),
        payload=invoice_payload(booking.id),
        currency=STARS,
        prices=[LabeledPrice(label=t.INVOICE_TITLE, amount=booking.deposit_stars)],
    )


async def refund_charge(bot: Bot, user_id: int, charge_id: str) -> bool:
    """Give one payment back; False (and logged) if Telegram refuses."""
    try:
        await bot.refund_star_payment(user_id=user_id, telegram_payment_charge_id=charge_id)
    except TelegramAPIError as e:
        if ALREADY_REFUNDED in str(e):
            return True
        log.error("Refund of payment %s to user %s failed: %s", charge_id, user_id, e)
        return False
    return True


async def refund(bot: Bot, session: AsyncSession, booking: Booking) -> bool:
    """Give the booking's payment back. The caller marks it refund_owed first, so if Telegram
    refuses, it stays owed and the reminder loop tries again."""
    if not await refund_charge(bot, booking.user_id, booking.payment_charge_id):
        return False
    booking.refunded = True
    booking.refund_owed = False
    await session.commit()
    return True


async def alert_refund_failed(
    bot: Bot, session: AsyncSession, booking: Booking, admin_ids: Iterable[int], tz: ZoneInfo
) -> None:
    """Tell the admins once that a refund failed; the reminder loop keeps retrying it."""
    await notify_admins(
        bot,
        session,
        admin_ids,
        lambda at: at.ADMIN_REFUND_FAILED.format(
            stars=booking.deposit_stars,
            client=user_link(booking.user_id, booking.user_name),
            booking=at.fmt_booking(booking, tz),
        ),
    )

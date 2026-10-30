"""Background jobs: visit reminders, releasing unpaid holds and retrying failed refunds."""

import asyncio
import logging
from datetime import timedelta
from zoneinfo import ZoneInfo

from aiogram import Bot
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker

from shared.notify import safe_send
from slotbook import payments, repo, scheduling
from slotbook.models import Booking, BookingStatus
from slotbook.scheduling import now_utc

log = logging.getLogger(__name__)

CHECK_INTERVAL_SEC = 60
# Failed refunds are retried every this many checks (and right after start): often enough
# to return money soon, rarely enough not to hammer Telegram if one keeps failing
REFUND_RETRY_EVERY = 10

# (flag column, how long before the visit, text attribute). The 2h check runs first: if both
# are due at once (booking made late), only the 2h reminder is sent.
REMINDERS = [
    (Booking.reminded_2h, timedelta(hours=2), "REMIND_2H"),
    (Booking.reminded_24h, timedelta(hours=24), "REMIND_24H"),
]


async def send_due_reminders(bot: Bot, session_factory: async_sessionmaker, tz: ZoneInfo) -> None:
    now = now_utc()
    async with session_factory() as session:
        for flag, before, text_name in REMINDERS:
            due = await session.scalars(
                select(Booking).where(
                    Booking.status == BookingStatus.ACTIVE,
                    flag.is_(False),
                    Booking.starts_at > now,
                    Booking.starts_at <= now + before,
                )
            )
            for booking in due:
                t = await repo.texts_for(session, booking.user_id)
                template = getattr(t, text_name)
                await safe_send(
                    bot, booking.user_id, template.format(booking=t.fmt_booking(booking, tz))
                )
                setattr(booking, flag.key, True)
                if flag is Booking.reminded_2h:
                    booking.reminded_24h = True
            await session.commit()


async def release_unpaid_holds(bot: Bot, session_factory: async_sessionmaker, tz: ZoneInfo) -> None:
    now = now_utc()
    async with session_factory() as session:
        for booking in await repo.expire_unpaid(session, now - payments.HOLD_TIME):
            # Otherwise the same client could take the slot again at once and keep it blocked
            scheduling.start_cooldown(booking.user_id, now)
            t = await repo.texts_for(session, booking.user_id)
            await safe_send(
                bot, booking.user_id, t.PAY_HOLD_EXPIRED.format(booking=t.fmt_booking(booking, tz))
            )


async def retry_refunds(bot: Bot, session_factory: async_sessionmaker, tz: ZoneInfo) -> None:
    """Refunds Telegram refused earlier, or that a restart interrupted. Only bookings marked
    refund_owed are tried, so a deposit kept after a late cancellation never goes back."""
    async with session_factory() as session:
        for booking in await repo.owed_refunds(session):
            if not await payments.refund(bot, session, booking):
                continue
            t = await repo.texts_for(session, booking.user_id)
            await safe_send(
                bot,
                booking.user_id,
                t.REFUND_DONE.format(
                    stars=booking.deposit_stars, booking=t.fmt_booking(booking, tz)
                ),
            )


async def reminder_loop(bot: Bot, session_factory: async_sessionmaker, tz: ZoneInfo) -> None:
    """Background jobs: every minute reminders and releasing unpaid holds, every
    REFUND_RETRY_EVERY minutes refunds that failed before."""
    check = 0
    while True:
        jobs = [release_unpaid_holds, send_due_reminders]
        if check % REFUND_RETRY_EVERY == 0:
            jobs.append(retry_refunds)
        for job in jobs:
            # One failing job must not stop the others
            try:
                await job(bot, session_factory, tz)
            except Exception:
                log.exception("Background job %s failed", job.__name__)
        check += 1
        await asyncio.sleep(CHECK_INTERVAL_SEC)

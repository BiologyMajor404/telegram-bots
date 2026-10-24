import asyncio
import logging
from datetime import timedelta
from zoneinfo import ZoneInfo

from aiogram import Bot
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker

from shared.notify import safe_send
from slotbook import payments, repo
from slotbook.models import Booking, BookingStatus
from slotbook.scheduling import now_utc

log = logging.getLogger(__name__)

CHECK_INTERVAL_SEC = 60

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
    async with session_factory() as session:
        for booking in await repo.expire_unpaid(session, now_utc() - payments.HOLD_TIME):
            t = await repo.texts_for(session, booking.user_id)
            await safe_send(
                bot, booking.user_id, t.PAY_HOLD_EXPIRED.format(booking=t.fmt_booking(booking, tz))
            )


async def reminder_loop(bot: Bot, session_factory: async_sessionmaker, tz: ZoneInfo) -> None:
    """Background jobs that run every minute: reminders and releasing unpaid holds."""
    while True:
        try:
            await release_unpaid_holds(bot, session_factory, tz)
            await send_due_reminders(bot, session_factory, tz)
        except Exception:
            log.exception("Reminder check failed")
        await asyncio.sleep(CHECK_INTERVAL_SEC)

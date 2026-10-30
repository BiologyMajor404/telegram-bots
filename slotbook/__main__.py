"""Entry point of SlotBook: `python -m slotbook`."""

import asyncio
import logging

from aiogram import Dispatcher
from aiogram.types import BotCommand

from shared.bot_setup import create_bot, on_error, publish_profile, set_commands
from shared.db import init_db
from shared.i18n import LangMiddleware, set_profile_texts
from shared.log_setup import setup_logging
from shared.middlewares import DbSessionMiddleware, StaleButtonMiddleware
from shared.storage import make_storage
from slotbook import repo
from slotbook.config import SlotBookSettings
from slotbook.handlers import admin, client, payments
from slotbook.i18n import resolve_lang
from slotbook.reminders import reminder_loop
from slotbook.texts import TEXTS, Ru

log = logging.getLogger("slotbook")


def commands(t: Ru) -> list[BotCommand]:
    return [
        BotCommand(command="start", description=t.CMD_START),
        BotCommand(command="language", description=t.CMD_LANGUAGE),
        BotCommand(command="paysupport", description=t.CMD_PAYSUPPORT),
    ]


async def main() -> None:
    settings = SlotBookSettings()
    setup_logging(settings.log_level)
    Ru.currency = settings.currency  # shared by all language subclasses
    if not settings.admin_ids:
        log.warning("SLOTBOOK_ADMIN_IDS is empty: nobody will get the master panel")

    # DBs created before migrations were added already have the 0001 schema
    engine, session_factory = await init_db(
        settings.database_url, "slotbook:migrations", baseline=("0001", "bookings")
    )
    async with session_factory() as session:
        await repo.seed_defaults(session)

    bot = create_bot(settings.token)
    dp = Dispatcher(
        storage=make_storage(settings.redis_url, prefix="slotbook"),
        admin_ids=settings.admin_ids,
        tz=settings.tz,
        support_contact=settings.support_contact,
    )
    dp.update.middleware(DbSessionMiddleware(session_factory))
    dp.update.middleware(LangMiddleware(resolve_lang, TEXTS))  # needs the DB session
    dp.callback_query.outer_middleware(StaleButtonMiddleware())
    dp.errors.register(on_error)
    # Admin router goes first so its FSM steps win over the client fallback handler
    dp.include_routers(admin.router, payments.router, client.router)

    # In the background: Telegram may rate-limit these, which must not stop the bot
    profile = asyncio.create_task(
        publish_profile(
            lambda: set_commands(bot, TEXTS, private=commands),
            lambda: set_profile_texts(bot, TEXTS),
        )
    )
    reminders = asyncio.create_task(reminder_loop(bot, session_factory, settings.tz))
    log.info("SlotBook started")
    try:
        await dp.start_polling(bot)
    finally:
        profile.cancel()
        reminders.cancel()
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())

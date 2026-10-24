import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import BotCommand, ErrorEvent

from shared.db import init_db
from shared.i18n import RUSSIAN_SPEAKING, LangMiddleware
from shared.log_setup import setup_logging
from shared.middlewares import DbSessionMiddleware
from shared.storage import make_storage
from slotbook import repo
from slotbook.config import SlotBookSettings
from slotbook.handlers import admin, client, payments
from slotbook.i18n import resolve_lang
from slotbook.reminders import reminder_loop
from slotbook.texts import TEXTS, Ru

log = logging.getLogger("slotbook")


async def on_error(event: ErrorEvent) -> bool:
    # Pressing the same button twice tries to set identical text; that's harmless
    if isinstance(event.exception, TelegramBadRequest) and "message is not modified" in str(
        event.exception
    ):
        if event.update.callback_query:
            await event.update.callback_query.answer()
        return True
    log.exception("Unhandled error", exc_info=event.exception)
    return True


def commands(t: Ru) -> list[BotCommand]:
    return [
        BotCommand(command="start", description=t.CMD_START),
        BotCommand(command="language", description=t.CMD_LANGUAGE),
        BotCommand(command="paysupport", description=t.CMD_PAYSUPPORT),
    ]


async def set_commands(bot: Bot) -> None:
    # English by default, Russian for the same app languages `detect` maps to Russian
    await bot.set_my_commands(commands(TEXTS["en"]))
    for code in RUSSIAN_SPEAKING:
        await bot.set_my_commands(commands(TEXTS["ru"]), language_code=code)


async def main() -> None:
    settings = SlotBookSettings()
    setup_logging(settings.log_level)
    if not settings.admin_ids:
        log.warning("SLOTBOOK_ADMIN_IDS is empty: nobody will get the master panel")

    # DBs created before migrations were added already have the 0001 schema
    engine, session_factory = await init_db(
        settings.database_url, "slotbook:migrations", baseline=("0001", "bookings")
    )
    async with session_factory() as session:
        await repo.seed_defaults(session)

    bot = Bot(
        settings.token.get_secret_value(),
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(
        storage=make_storage(settings.redis_url, prefix="slotbook"),
        admin_ids=settings.admin_ids,
        tz=settings.tz,
    )
    dp.update.middleware(DbSessionMiddleware(session_factory))
    dp.update.middleware(LangMiddleware(resolve_lang, TEXTS))  # needs the DB session
    dp.errors.register(on_error)
    # Admin router goes first so its FSM steps win over the client fallback handler
    dp.include_routers(admin.router, payments.router, client.router)

    await set_commands(bot)
    reminders = asyncio.create_task(reminder_loop(bot, session_factory, settings.tz))
    log.info("SlotBook started")
    try:
        await dp.start_polling(bot)
    finally:
        reminders.cancel()
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import BotCommand, BotCommandScopeAllGroupChats, ErrorEvent

from shared.db import init_db
from shared.log_setup import setup_logging
from shared.middlewares import DbSessionMiddleware
from splitmate.config import SplitMateSettings
from splitmate.handlers import group, inline, private

log = logging.getLogger("splitmate")

GROUP_COMMANDS = [
    BotCommand(command="add", description="Записать расход: /add 3000 такси"),
    BotCommand(command="balance", description="Кто кому должен"),
    BotCommand(command="history", description="Последние расходы"),
    BotCommand(command="join", description="Участвовать в расходах"),
    BotCommand(command="members", description="Участники"),
    BotCommand(command="currency", description="Валюта чата"),
    BotCommand(command="help", description="Как пользоваться"),
]


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


async def main() -> None:
    settings = SplitMateSettings()
    setup_logging(settings.log_level)
    engine, session_factory = await init_db(settings.database_url, "splitmate:migrations")

    bot = Bot(
        settings.token.get_secret_value(),
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    # No multi-step dialogs here, so the default in-memory FSM storage is enough
    dp = Dispatcher()
    dp.update.middleware(DbSessionMiddleware(session_factory))
    dp.errors.register(on_error)
    dp.include_routers(group.router, private.router, inline.router)

    await bot.set_my_commands(GROUP_COMMANDS, scope=BotCommandScopeAllGroupChats())
    await bot.set_my_commands([BotCommand(command="start", description="Как начать")])
    log.info("SplitMates started")
    try:
        await dp.start_polling(bot)
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())

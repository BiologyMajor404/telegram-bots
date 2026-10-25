import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import BotCommand, BotCommandScopeAllGroupChats, ErrorEvent

from shared.db import init_db
from shared.i18n import LangMiddleware, command_locales, set_profile_texts
from shared.log_setup import setup_logging
from shared.middlewares import DbSessionMiddleware
from shared.storage import make_storage
from splitmate.config import SplitMateSettings
from splitmate.handlers import group, inline, private
from splitmate.i18n import resolve_lang
from splitmate.texts import TEXTS, Ru

log = logging.getLogger("splitmate")


def group_commands(t: Ru) -> list[BotCommand]:
    return [
        BotCommand(command="add", description=t.CMD_ADD),
        BotCommand(command="balance", description=t.CMD_BALANCE),
        BotCommand(command="history", description=t.CMD_HISTORY),
        BotCommand(command="join", description=t.CMD_JOIN),
        BotCommand(command="members", description=t.CMD_MEMBERS),
        BotCommand(command="currency", description=t.CMD_CURRENCY),
        BotCommand(command="language", description=t.CMD_LANGUAGE),
        BotCommand(command="help", description=t.CMD_HELP),
    ]


async def set_commands(bot: Bot) -> None:
    # Each Telegram app language gets the command lists in the language `detect` gives it
    for lang, codes in command_locales().items():
        t = TEXTS[lang]
        for code in codes:
            await bot.set_my_commands(
                group_commands(t), scope=BotCommandScopeAllGroupChats(), language_code=code
            )
            await bot.set_my_commands(
                [BotCommand(command="start", description=t.CMD_START)], language_code=code
            )


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
    # FSM keeps the "enter an amount" step; Redis lets it survive restarts
    dp = Dispatcher(storage=make_storage(settings.redis_url, prefix="splitmate"))
    dp.update.middleware(DbSessionMiddleware(session_factory))
    dp.update.middleware(LangMiddleware(resolve_lang, TEXTS))  # needs the DB session
    dp.errors.register(on_error)
    dp.include_routers(group.router, private.router, inline.router)

    await set_commands(bot)
    await set_profile_texts(bot, TEXTS)
    log.info("SplitMates started")
    try:
        await dp.start_polling(bot)
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())

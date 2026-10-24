import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import BotCommand, BotCommandScopeAllGroupChats, ErrorEvent

from chatguard.ai import Classifier
from chatguard.config import ChatGuardSettings
from chatguard.handlers import group, private
from chatguard.i18n import resolve_lang
from chatguard.texts import TEXTS, Ru
from shared.db import init_db
from shared.i18n import LangMiddleware, command_locales
from shared.log_setup import setup_logging
from shared.middlewares import DbSessionMiddleware

log = logging.getLogger("chatguard")


def group_commands(t: Ru) -> list[BotCommand]:
    return [
        BotCommand(command="settings", description=t.CMD_SETTINGS),
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
    settings = ChatGuardSettings()
    setup_logging(settings.log_level)
    engine, session_factory = await init_db(settings.database_url, "chatguard:migrations")

    api_key = settings.anthropic_api_key.get_secret_value()
    classifier = Classifier(api_key) if api_key else None
    if classifier is None:
        log.warning("ANTHROPIC_API_KEY is empty: only the fast rules will check messages")

    bot = Bot(
        settings.token.get_secret_value(),
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(classifier=classifier, ai_daily_limit=settings.ai_daily_limit)
    dp.update.middleware(DbSessionMiddleware(session_factory))
    dp.update.middleware(LangMiddleware(resolve_lang, TEXTS))  # needs the DB session
    dp.errors.register(on_error)
    dp.include_routers(group.router, private.router)

    await set_commands(bot)
    log.info("ChatGuard AI started (AI: %s)", "on" if classifier else "off")
    try:
        await dp.start_polling(bot)
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())

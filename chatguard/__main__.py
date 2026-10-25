"""Entry point of ChatGuard AI: `python -m chatguard`."""

import asyncio
import logging

from aiogram import Dispatcher
from aiogram.types import BotCommand

from chatguard.ai import Classifier
from chatguard.config import ChatGuardSettings
from chatguard.handlers import group, payments, private
from chatguard.i18n import resolve_lang
from chatguard.texts import TEXTS, Ru
from shared.bot_setup import create_bot, on_error, set_commands
from shared.db import init_db
from shared.i18n import LangMiddleware, set_profile_texts
from shared.log_setup import setup_logging
from shared.middlewares import DbSessionMiddleware

log = logging.getLogger("chatguard")


def private_commands(t: Ru) -> list[BotCommand]:
    return [
        BotCommand(command="start", description=t.CMD_START),
        BotCommand(command="paysupport", description=t.CMD_PAYSUPPORT),
    ]


def group_commands(t: Ru) -> list[BotCommand]:
    return [
        BotCommand(command="settings", description=t.CMD_SETTINGS),
        BotCommand(command="pro", description=t.CMD_PRO),
        BotCommand(command="language", description=t.CMD_LANGUAGE),
        BotCommand(command="help", description=t.CMD_HELP),
    ]


async def main() -> None:
    settings = ChatGuardSettings()
    setup_logging(settings.log_level)
    engine, session_factory = await init_db(settings.database_url, "chatguard:migrations")

    api_key = settings.anthropic_api_key.get_secret_value()
    classifier = Classifier(api_key) if api_key else None
    if classifier is None:
        log.warning("ANTHROPIC_API_KEY is empty: only the fast rules will check messages")

    bot = create_bot(settings.token)
    dp = Dispatcher(
        classifier=classifier,
        plans=settings.plans,
        support_contact=settings.support_contact,
    )
    dp.update.middleware(DbSessionMiddleware(session_factory))
    dp.update.middleware(LangMiddleware(resolve_lang, TEXTS))  # needs the DB session
    dp.errors.register(on_error)
    # Payments first: payment messages arrive in private chats, where the catch-all lives
    dp.include_routers(payments.router, group.router, private.router)

    await set_commands(bot, TEXTS, private=private_commands, group=group_commands)
    await set_profile_texts(bot, TEXTS)
    log.info("ChatGuard AI started (AI: %s)", "on" if classifier else "off")
    try:
        await dp.start_polling(bot)
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())

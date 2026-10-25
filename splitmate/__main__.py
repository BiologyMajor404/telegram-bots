"""Entry point of SplitMates: `python -m splitmate`."""

import asyncio
import logging

from aiogram import Dispatcher
from aiogram.types import BotCommand

from shared.bot_setup import create_bot, on_error, set_commands
from shared.db import init_db
from shared.i18n import LangMiddleware, set_profile_texts
from shared.log_setup import setup_logging
from shared.middlewares import DbSessionMiddleware
from shared.storage import make_storage
from splitmate.config import SplitMateSettings
from splitmate.handlers import group, inline, private
from splitmate.i18n import resolve_lang
from splitmate.texts import TEXTS, Ru

log = logging.getLogger("splitmate")


def private_commands(t: Ru) -> list[BotCommand]:
    return [BotCommand(command="start", description=t.CMD_START)]


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


async def main() -> None:
    settings = SplitMateSettings()
    setup_logging(settings.log_level)
    engine, session_factory = await init_db(settings.database_url, "splitmate:migrations")

    bot = create_bot(settings.token)
    # FSM keeps the "enter an amount" step; Redis lets it survive restarts
    dp = Dispatcher(storage=make_storage(settings.redis_url, prefix="splitmate"))
    dp.update.middleware(DbSessionMiddleware(session_factory))
    dp.update.middleware(LangMiddleware(resolve_lang, TEXTS))  # needs the DB session
    dp.errors.register(on_error)
    dp.include_routers(group.router, private.router, inline.router)

    await set_commands(bot, TEXTS, private=private_commands, group=group_commands)
    await set_profile_texts(bot, TEXTS)
    log.info("SplitMates started")
    try:
        await dp.start_polling(bot)
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())

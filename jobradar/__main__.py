"""Entry point of JobRadar: `python -m jobradar`."""

import asyncio
import logging

from aiogram import Dispatcher
from aiogram.types import BotCommand

from jobradar.ai import Analyzer
from jobradar.config import JobRadarSettings
from jobradar.handlers import admin, filters, payments, private
from jobradar.i18n import resolve_lang
from jobradar.plans import Access
from jobradar.radar import Radar
from jobradar.texts import TEXTS, Ru
from shared.bot_setup import create_bot, on_error, publish_profile, set_commands
from shared.db import init_db
from shared.i18n import LangMiddleware, set_profile_texts
from shared.log_setup import setup_logging
from shared.middlewares import DbSessionMiddleware, StaleButtonMiddleware
from shared.storage import make_storage

log = logging.getLogger("jobradar")


def commands(t: Ru) -> list[BotCommand]:
    return [
        BotCommand(command="start", description=t.CMD_START),
        BotCommand(command="settings", description=t.CMD_SETTINGS),
        BotCommand(command="filters", description=t.CMD_FILTERS),
        BotCommand(command="sources", description=t.CMD_SOURCES),
        BotCommand(command="mail", description=t.CMD_MAIL),
        BotCommand(command="pro", description=t.CMD_PRO),
        BotCommand(command="status", description=t.CMD_STATUS),
        BotCommand(command="language", description=t.CMD_LANGUAGE),
        BotCommand(command="paysupport", description=t.CMD_PAYSUPPORT),
    ]


async def main() -> None:
    settings = JobRadarSettings()
    setup_logging(settings.log_level)
    engine, session_factory = await init_db(settings.database_url, "jobradar:migrations")

    bot = create_bot(settings.token)
    access = Access(settings.plans, settings.admin_ids)
    radar = Radar(
        bot,
        session_factory,
        Analyzer(settings.anthropic_api_key.get_secret_value()),
        settings.channels,
        access,
        settings.ai_daily_limit,
        settings.tz,
        settings.freelancehunt_token.get_secret_value(),
        settings.mail,
    )
    dp = Dispatcher(
        # Redis keeps a half-done step ("type what to look for") over restarts, and memory
        # would hold a record for every user forever
        storage=make_storage(settings.redis_url, prefix="jobradar"),
        radar=radar,
        access=access,
        allowed_ids=settings.allowed_ids,
        poll_minutes=settings.poll_minutes,
        support_contact=settings.support_contact,
        mail=settings.mail,
    )
    dp.update.middleware(DbSessionMiddleware(session_factory))
    dp.update.middleware(LangMiddleware(resolve_lang, TEXTS))  # needs the DB session
    dp.callback_query.outer_middleware(StaleButtonMiddleware())
    dp.errors.register(on_error)
    # Payments first: payment messages arrive in private chats, where the catch-all lives
    dp.include_routers(payments.router, admin.router, filters.router, private.router)

    # In the background: Telegram may rate-limit these, which must not stop the bot
    profile = asyncio.create_task(
        publish_profile(
            lambda: set_commands(bot, TEXTS, private=commands),
            lambda: set_profile_texts(bot, TEXTS),
        )
    )
    search = asyncio.create_task(radar.run_forever(settings.poll_minutes))
    log.info(
        "JobRadar started: %d Telegram channels, every %d min",
        len(radar.channels),
        settings.poll_minutes,
    )
    try:
        await dp.start_polling(bot)
    finally:
        profile.cancel()
        search.cancel()
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())

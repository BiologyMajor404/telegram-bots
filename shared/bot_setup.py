"""Startup pieces every bot shares: the Bot object, the error handler and command menus."""

import logging
from collections.abc import Callable
from typing import Any

from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import BotCommand, BotCommandScopeAllGroupChats, ErrorEvent
from pydantic import SecretStr

from shared.i18n import command_locales

log = logging.getLogger(__name__)

# Builds a command menu from one language's texts
CommandsFor = Callable[[Any], list[BotCommand]]


def create_bot(token: SecretStr) -> Bot:
    """All bots format messages with HTML."""
    return Bot(token.get_secret_value(), default=DefaultBotProperties(parse_mode=ParseMode.HTML))


async def on_error(event: ErrorEvent) -> bool:
    """Swallow harmless errors, log the rest; the bot keeps running either way."""
    # Pressing the same button twice tries to set identical text
    if isinstance(event.exception, TelegramBadRequest) and "message is not modified" in str(
        event.exception
    ):
        if event.update.callback_query:
            await event.update.callback_query.answer()
        return True
    log.exception("Unhandled error", exc_info=event.exception)
    return True


async def set_commands(
    bot: Bot,
    catalog: dict[str, Any],
    private: CommandsFor,
    group: CommandsFor | None = None,
) -> None:
    """Command menus in each Telegram app language: `private` for private chats (and the
    default), `group` for group chats if the bot works there."""
    for lang, codes in command_locales().items():
        t = catalog[lang]
        for code in codes:
            await bot.set_my_commands(private(t), language_code=code)
            if group is not None:
                await bot.set_my_commands(
                    group(t), scope=BotCommandScopeAllGroupChats(), language_code=code
                )

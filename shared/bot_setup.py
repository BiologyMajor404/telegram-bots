"""Startup pieces every bot shares: the Bot object, the error handler and command menus."""

import asyncio
import contextlib
import logging
from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramAPIError, TelegramBadRequest, TelegramRetryAfter
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
    harmless = isinstance(event.exception, TelegramBadRequest) and "message is not modified" in str(
        event.exception
    )
    if not harmless:
        log.exception("Unhandled error", exc_info=event.exception)
    if event.update.callback_query:
        # Stop the button's spinner; fails harmlessly if the handler answered already
        with contextlib.suppress(TelegramAPIError):
            await event.update.callback_query.answer()
    return True


PROFILE_TRIES = 5


async def publish_profile(*steps: Callable[[], Awaitable[None]]) -> None:
    """Set command menus and profile texts without ever stopping the bot: run as a
    background task. Telegram rate-limits these calls, e.g. after several restarts in a row;
    then wait as long as it asks and try again. The previous texts stay meanwhile."""
    for step in steps:
        for _ in range(PROFILE_TRIES):
            try:
                await step()
                break
            except TelegramRetryAfter as e:
                log.warning("Telegram asks to wait %ss before updating the menus", e.retry_after)
                await asyncio.sleep(e.retry_after + 1)
            except TelegramAPIError as e:
                log.warning("Couldn't update the menus or profile texts: %s", e)
                break
        else:
            log.warning("Gave up updating the menus or profile texts after %d tries", PROFILE_TRIES)


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

"""Sending messages that may fail (blocked bot, deleted chat) without crashing."""

import asyncio
import logging
from collections.abc import Iterable

from aiogram import Bot
from aiogram.exceptions import (
    TelegramAPIError,
    TelegramNetworkError,
    TelegramRetryAfter,
    TelegramServerError,
)

log = logging.getLogger(__name__)

MAX_WAIT_SEC = 30  # a longer flood wait drops the message instead of stalling the caller


async def safe_send(bot: Bot, chat_id: int, text: str, **kwargs) -> bool:
    """Send a message, ignoring users who blocked the bot or never started it. A short flood
    wait or a network hiccup gets one more try, so a reminder isn't lost to a blip."""
    for attempt in range(2):
        try:
            await bot.send_message(chat_id, text, **kwargs)
            return True
        except TelegramRetryAfter as e:
            error, wait = e, e.retry_after
        except (TelegramNetworkError, TelegramServerError) as e:
            error, wait = e, 1
        except TelegramAPIError as e:  # blocked, chat gone, bad request: a retry won't help
            error, wait = e, None
        if attempt or wait is None or wait > MAX_WAIT_SEC:
            break
        await asyncio.sleep(wait)
    log.warning("Can't send message to %s: %s", chat_id, error)
    return False


async def notify_all(bot: Bot, chat_ids: Iterable[int], text: str, **kwargs) -> None:
    for chat_id in chat_ids:
        await safe_send(bot, chat_id, text, **kwargs)

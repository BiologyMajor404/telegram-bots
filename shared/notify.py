"""Sending messages that may fail (blocked bot, deleted chat) without crashing."""

import logging
from collections.abc import Iterable

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError

log = logging.getLogger(__name__)


async def safe_send(bot: Bot, chat_id: int, text: str, **kwargs) -> bool:
    """Send a message, ignoring users who blocked the bot or never started it."""
    try:
        await bot.send_message(chat_id, text, **kwargs)
        return True
    except TelegramAPIError as e:
        log.warning("Can't send message to %s: %s", chat_id, e)
        return False


async def notify_all(bot: Bot, chat_ids: Iterable[int], text: str, **kwargs) -> None:
    for chat_id in chat_ids:
        await safe_send(bot, chat_id, text, **kwargs)

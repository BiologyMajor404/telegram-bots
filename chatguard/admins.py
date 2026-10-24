"""Is this user an admin of the chat? Cached for a few minutes to spare Telegram API calls."""

import time

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError

CACHE_SEC = 300
_cache: dict[tuple[int, int], tuple[bool, float]] = {}


async def is_admin(bot: Bot, chat_id: int, user_id: int) -> bool:
    key = (chat_id, user_id)
    cached = _cache.get(key)
    if cached and time.monotonic() - cached[1] < CACHE_SEC:
        return cached[0]
    try:
        member = await bot.get_chat_member(chat_id, user_id)
        result = member.status in ("creator", "administrator")
    except TelegramAPIError:
        return False
    _cache[key] = (result, time.monotonic())
    return result

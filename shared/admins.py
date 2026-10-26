"""Is this user an admin of the chat? Cached briefly to spare Telegram API calls."""

import time

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError

# Short, so a demoted admin loses their rights within a minute
CACHE_SEC = 60
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

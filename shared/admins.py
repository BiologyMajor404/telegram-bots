"""Is this user an admin of the chat? Cached briefly to spare Telegram API calls."""

import logging
import time

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError
from aiogram.types import Message

log = logging.getLogger(__name__)

# Short, so a demoted admin loses their rights within a minute
CACHE_SEC = 60
CACHE_MAX = 10_000  # entries: past it, stale ones are dropped so the cache can't grow forever
_cache: dict[tuple[int, int], tuple[bool, float]] = {}


def _remember(key: tuple[int, int], result: bool, now: float) -> None:
    if len(_cache) >= CACHE_MAX:
        for stale in [k for k, (_, at) in _cache.items() if now - at >= CACHE_SEC]:
            del _cache[stale]
        if len(_cache) >= CACHE_MAX:  # all fresh, e.g. a raid: start over
            _cache.clear()
    _cache[key] = (result, now)


async def is_admin(bot: Bot, chat_id: int, user_id: int) -> bool:
    key = (chat_id, user_id)
    now = time.monotonic()
    cached = _cache.get(key)
    if cached and now - cached[1] < CACHE_SEC:
        return cached[0]
    try:
        member = await bot.get_chat_member(chat_id, user_id)
    except TelegramAPIError as e:
        log.warning("Can't check whether %s is an admin of %s: %s", user_id, chat_id, e)
        return False
    result = member.status in ("creator", "administrator")
    _remember(key, result, now)
    return result


async def sender_is_admin(bot: Bot, message: Message) -> bool:
    """Whether a group message comes from an admin. Anonymous admins post as the group
    itself (from_user is then a placeholder bot), so they count too; posts on behalf of
    any other chat, e.g. a channel, don't."""
    if message.sender_chat is not None:
        return message.sender_chat.id == message.chat.id
    return await is_admin(bot, message.chat.id, message.from_user.id)

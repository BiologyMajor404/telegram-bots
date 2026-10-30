"""Where conversation state (FSM) is kept: Redis, or memory as a fallback."""

import logging
from datetime import timedelta

from aiogram.fsm.storage.base import BaseStorage, DefaultKeyBuilder
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.storage.redis import RedisStorage
from redis.asyncio import Redis

log = logging.getLogger(__name__)

# An unfinished step ("send the amount") is forgotten after this, so a step someone walked
# away from can't catch their unrelated messages days later
STATE_TTL = timedelta(hours=1)


def make_storage(redis_url: str, prefix: str) -> BaseStorage:
    """FSM storage: Redis in production (survives restarts), memory if Redis isn't configured."""
    if not redis_url:
        log.warning("REDIS_URL is empty, FSM state will be lost on restart")
        return MemoryStorage()
    return RedisStorage(
        Redis.from_url(redis_url),
        key_builder=DefaultKeyBuilder(prefix=prefix),
        state_ttl=STATE_TTL,
        data_ttl=STATE_TTL,
    )

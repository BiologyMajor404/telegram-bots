"""Shared helpers: sending with a retry, masked tokens in logs, admins, old buttons."""

import asyncio
import logging
from types import SimpleNamespace
from unittest.mock import AsyncMock

from aiogram.exceptions import TelegramForbiddenError, TelegramRetryAfter
from aiogram.methods import SendMessage
from aiogram.types import Chat, InaccessibleMessage

from shared import admins, notify
from shared.log_setup import RedactingFormatter
from shared.middlewares import StaleButtonMiddleware

METHOD = SendMessage(chat_id=1, text="hi")


class FakeBot:
    def __init__(self, *errors: Exception) -> None:
        self.errors = list(errors)
        self.sent = 0

    async def send_message(self, chat_id, text, **kwargs):
        if self.errors:
            raise self.errors.pop(0)
        self.sent += 1


def test_a_short_flood_wait_gets_one_more_try(monkeypatch):
    monkeypatch.setattr(notify.asyncio, "sleep", AsyncMock())
    bot = FakeBot(TelegramRetryAfter(METHOD, "Too Many Requests", retry_after=3))
    assert asyncio.run(notify.safe_send(bot, 1, "reminder"))
    assert bot.sent == 1


def test_a_blocked_user_is_not_retried():
    bot = FakeBot(TelegramForbiddenError(METHOD, "bot was blocked by the user"))
    assert not asyncio.run(notify.safe_send(bot, 1, "reminder"))


def test_a_long_flood_wait_drops_the_message(monkeypatch):
    sleep = AsyncMock()
    monkeypatch.setattr(notify.asyncio, "sleep", sleep)
    bot = FakeBot(TelegramRetryAfter(METHOD, "Too Many Requests", retry_after=600))
    assert not asyncio.run(notify.safe_send(bot, 1, "reminder"))
    sleep.assert_not_called()


def test_bot_tokens_are_masked_in_logs():
    record = logging.LogRecord(
        "aiogram", logging.ERROR, "", 0, "url='https://api.telegram.org/bot%s/getMe'", None, None
    )
    record.args = ("123456789:" + "A" * 35,)  # the shape of a token, not a real one
    line = RedactingFormatter("%(message)s").format(record)
    assert line == "url='https://api.telegram.org/bot<token>/getMe'"


def test_anonymous_admins_count_as_admins():
    group = SimpleNamespace(id=-100)
    anonymous = SimpleNamespace(chat=group, sender_chat=group, from_user=None)
    channel = SimpleNamespace(chat=group, sender_chat=SimpleNamespace(id=-200), from_user=None)
    assert asyncio.run(admins.sender_is_admin(None, anonymous))
    assert not asyncio.run(admins.sender_is_admin(None, channel))


def test_the_admin_cache_cannot_grow_forever(monkeypatch):
    monkeypatch.setattr(admins, "CACHE_MAX", 3)
    monkeypatch.setattr(admins, "_cache", {})
    for user_id in range(10):
        admins._remember((1, user_id), False, now=1000.0)
    assert len(admins._cache) <= 3


def test_a_button_under_a_vanished_message_gets_a_notice():
    gone = InaccessibleMessage(chat=Chat(id=1, type="private"), message_id=5)
    cb = SimpleNamespace(message=gone, answer=AsyncMock())
    handler = AsyncMock()
    asyncio.run(StaleButtonMiddleware()(handler, cb, {"lang": "en"}))
    handler.assert_not_called()
    assert "out of date" in cb.answer.call_args.args[0]

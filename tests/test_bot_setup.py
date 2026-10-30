"""Menus and profile texts are set in the background and never stop a bot."""

import asyncio

from aiogram.exceptions import TelegramBadRequest, TelegramRetryAfter
from aiogram.methods import SetMyCommands

from shared import bot_setup

METHOD = SetMyCommands(commands=[])


def test_waits_out_telegram_rate_limit_then_retries(monkeypatch):
    waits, calls = [], []

    async def fake_sleep(seconds):
        waits.append(seconds)

    async def step():
        calls.append(1)
        if len(calls) == 1:
            raise TelegramRetryAfter(METHOD, "Too Many Requests", retry_after=44)

    monkeypatch.setattr(bot_setup.asyncio, "sleep", fake_sleep)
    asyncio.run(bot_setup.publish_profile(step))
    assert waits == [45]
    assert len(calls) == 2


def test_other_errors_skip_the_step_but_not_the_rest():
    done = []

    async def broken():
        raise TelegramBadRequest(METHOD, "bad")

    async def fine():
        done.append(1)

    asyncio.run(bot_setup.publish_profile(broken, fine))  # no exception
    assert done == [1]

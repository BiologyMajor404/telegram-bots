"""Middlewares every bot shares: a database session per update, and old buttons."""

from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, InaccessibleMessage, TelegramObject
from sqlalchemy.ext.asyncio import async_sessionmaker

from shared.i18n import STALE_BUTTON


class DbSessionMiddleware(BaseMiddleware):
    """Opens a DB session per update and passes it to handlers as `session`."""

    def __init__(self, session_factory: async_sessionmaker) -> None:
        self.session_factory = session_factory

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        async with self.session_factory() as session:
            data["session"] = session
            return await handler(event, data)


class StaleButtonMiddleware(BaseMiddleware):
    """A button under a message Telegram no longer shows the bot (deleted, or too old): the
    handlers would fail editing it, so the user is asked to send the command again.
    Register as `dp.callback_query.outer_middleware(...)`, after the language middleware."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: CallbackQuery,
        data: dict[str, Any],
    ) -> Any:
        if isinstance(event.message, InaccessibleMessage):
            text = STALE_BUTTON.get(data.get("lang", "en"), STALE_BUTTON["en"])
            await event.answer(text, show_alert=True)
            return None
        return await handler(event, data)

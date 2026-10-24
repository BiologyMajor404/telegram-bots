"""Language selection shared by all bots.

Each bot keeps its texts as a class per language (English subclasses Russian), and this
middleware puts the right one into handler data as `t` (and the code as `lang`)."""

from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardMarkup, TelegramObject
from aiogram.utils.keyboard import InlineKeyboardBuilder

LANGS = ("ru", "en")
LANG_NAMES = {"ru": "🇷🇺 Русский", "en": "🇬🇧 English"}
# Telegram app languages whose users usually prefer the Russian interface
RUSSIAN_SPEAKING = {"ru", "uk", "be", "kk"}

Resolver = Callable[[dict[str, Any]], Awaitable[str]]


def detect(language_code: str | None) -> str:
    """Telegram app language -> interface language: Russian-speaking -> ru, anyone else -> en."""
    if language_code and language_code.split("-")[0].lower() in RUSSIAN_SPEAKING:
        return "ru"
    return "en"


class SetLang(CallbackData, prefix="lang"):
    code: str


def lang_keyboard() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for code in LANGS:
        b.button(text=LANG_NAMES[code], callback_data=SetLang(code=code))
    return b.as_markup()


class LangMiddleware(BaseMiddleware):
    """Resolves the language for each update and passes `lang` and `t` to handlers."""

    def __init__(self, resolve: Resolver, catalog: dict[str, Any]) -> None:
        self.resolve = resolve
        self.catalog = catalog

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        lang = await self.resolve(data)
        data["lang"] = lang
        data["t"] = self.catalog[lang]
        return await handler(event, data)

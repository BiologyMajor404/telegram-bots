"""Language selection shared by all bots.

Each bot keeps its texts as a class per language (the others subclass Russian), and
this middleware puts the right one into handler data as `t` (and the code as `lang`)."""

from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardMarkup, TelegramObject
from aiogram.utils.keyboard import InlineKeyboardBuilder

LANGS = ("uk", "ru", "pl", "en")
LANG_NAMES = {"uk": "🇺🇦 Українська", "ru": "🇷🇺 Русский", "pl": "🇵🇱 Polski", "en": "🇬🇧 English"}
# Telegram app language -> interface language; anything not listed gets English
APP_LANGUAGES = {"uk": "uk", "ru": "ru", "be": "ru", "kk": "ru", "pl": "pl"}
# Same text in every language, so a user who can't read the current one still finds the switch
LANGUAGE_BUTTON = "🌐 Мова / Язык / Język / Language"
CHOOSE_LANGUAGE = "🌐 Оберіть мову / Выберите язык / Wybierz język / Choose language:"


def command_locales() -> dict[str, list[str | None]]:
    """Interface language -> Telegram language codes its command list is shown for
    (None = the default list for everyone else)."""
    locales: dict[str, list[str | None]] = {"en": [None]}
    for app_code, lang in APP_LANGUAGES.items():
        locales.setdefault(lang, []).append(app_code)
    return locales


Resolver = Callable[[dict[str, Any]], Awaitable[str]]


def detect(language_code: str | None) -> str:
    """Telegram app language -> interface language (one of LANGS)."""
    if not language_code:
        return "en"
    return APP_LANGUAGES.get(language_code.split("-")[0].lower(), "en")


class SetLang(CallbackData, prefix="lang"):
    code: str


def lang_keyboard() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for code in LANGS:
        b.button(text=LANG_NAMES[code], callback_data=SetLang(code=code))
    b.adjust(2)
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

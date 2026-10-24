"""How SlotBook picks the language: the user's saved choice, else their Telegram language."""

from collections.abc import Callable, Iterable
from typing import Any

from aiogram import Bot
from sqlalchemy.ext.asyncio import AsyncSession

from shared.i18n import detect
from shared.notify import safe_send
from slotbook import repo
from slotbook.texts import Ru


async def resolve_lang(data: dict[str, Any]) -> str:
    user = data.get("event_from_user")
    if user is None:
        return "ru"
    session = data["session"]
    lang = await repo.get_lang(session, user.id)
    if lang is None:
        lang = detect(user.language_code)
        # Saved right away so reminders and notifications use it too
        await repo.set_lang(session, user.id, lang)
    return lang


async def notify_admins(
    bot: Bot, session: AsyncSession, admin_ids: Iterable[int], build: Callable[[Ru], str]
) -> None:
    """Send each admin a message in their own language; `build(t)` returns the text."""
    for admin_id in admin_ids:
        await safe_send(bot, admin_id, build(await repo.texts_for(session, admin_id)))

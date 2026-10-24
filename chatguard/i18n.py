"""How ChatGuard picks the language: a group has one stored language,
private chats follow the user's Telegram language."""

from typing import Any

from chatguard import repo
from shared.i18n import detect

GROUPS = {"group", "supergroup"}


async def resolve_lang(data: dict[str, Any]) -> str:
    user = data.get("event_from_user")
    fallback = detect(user.language_code if user else None)
    chat = data.get("event_chat")
    if chat is not None and chat.type in GROUPS:
        stored = await repo.ensure_chat(data["session"], chat.id, chat.title, fallback)
        return stored.lang
    return fallback

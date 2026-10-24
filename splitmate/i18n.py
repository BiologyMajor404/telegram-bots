"""How SplitMates picks the language: a group chat has one shared language (stored),
private chats and inline queries follow the user's Telegram language."""

from typing import Any

from shared.i18n import detect
from splitmate import repo

GROUPS = {"group", "supergroup"}


async def resolve_lang(data: dict[str, Any]) -> str:
    user = data.get("event_from_user")
    fallback = detect(user.language_code if user else None)
    chat = data.get("event_chat")
    if chat is not None and chat.type in GROUPS:
        # The first person to talk to the bot in a group sets the chat's initial language
        stored = await repo.ensure_chat(data["session"], chat.id, chat.title, fallback)
        return stored.lang
    return fallback

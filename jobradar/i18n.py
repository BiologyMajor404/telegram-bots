"""How JobRadar picks the language: the stored one for subscribers, else the Telegram app's."""

from typing import Any

from jobradar import repo
from shared.i18n import detect


async def resolve_lang(data: dict[str, Any]) -> str:
    user = data.get("event_from_user")
    if user is None:
        return "en"
    sub = await repo.get_subscriber(data["session"], user.id)
    return sub.lang if sub else detect(user.language_code)

"""What the bot and the admins may do in a chat, read from their admin rights."""

import logging
import time
from dataclasses import dataclass

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError
from aiogram.types import ChatMember, ChatMemberAdministrator, ChatMemberOwner

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class Rights:
    delete: bool  # delete other people's messages
    restrict: bool  # mute and ban ("Ban users")


NO_RIGHTS = Rights(delete=False, restrict=False)
# Short, so rights granted after a "give me the rights" notice work within a minute
BOT_RIGHTS_SEC = 60
CACHE_MAX = 10_000  # chats: past it the cache starts over, so it can't grow forever
_bot_rights: dict[int, tuple[Rights, float]] = {}


def rights_of(member: ChatMember) -> Rights:
    if isinstance(member, ChatMemberOwner):
        return Rights(delete=True, restrict=True)
    if isinstance(member, ChatMemberAdministrator):
        return Rights(delete=member.can_delete_messages, restrict=member.can_restrict_members)
    return NO_RIGHTS


async def bot_rights(bot: Bot, chat_id: int, *, fresh: bool = False) -> Rights:
    """The bot's own rights in a chat, cached briefly; `fresh` asks Telegram again."""
    now = time.monotonic()
    cached = _bot_rights.get(chat_id)
    if cached and not fresh and now - cached[1] < BOT_RIGHTS_SEC:
        return cached[0]
    try:
        rights = rights_of(await bot.get_chat_member(chat_id, bot.id))
    except TelegramAPIError as e:
        log.warning("Can't check the bot's rights in %s: %s", chat_id, e)
        return NO_RIGHTS
    if len(_bot_rights) >= CACHE_MAX:
        _bot_rights.clear()
    _bot_rights[chat_id] = (rights, now)
    return rights


async def can_restore(bot: Bot, chat_id: int, user_id: int) -> bool:
    """Restore lifts mutes and bans, so it takes the admin right to ban users (the owner
    has every right). Asked fresh each time: it's pressed rarely."""
    try:
        member = await bot.get_chat_member(chat_id, user_id)
    except TelegramAPIError as e:
        log.warning("Can't check the rights of %s in %s: %s", user_id, chat_id, e)
        return False
    return rights_of(member).restrict

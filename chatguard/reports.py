"""What the bot tells the admins about a catch. Names and AI reasons come from strangers, so
they lose anything Telegram would turn into a link, and every text fits into one message."""

import re
from dataclasses import dataclass
from html import escape

from chatguard.models import Action, is_channel
from chatguard.texts import Ru
from shared.formatting import user_link

NAME_LIMIT = 64
MESSAGE_LIMIT = 4096  # Telegram counts UTF-16 code units, and an emoji takes two
# A word Telegram would make clickable: an @handle (or e-mail), a URL, a domain like scam.xyz
LINKISH = re.compile(r"@|://|www\.|\w\.[^\W\d_]{2,}", re.IGNORECASE)


@dataclass(frozen=True)
class Outcome:
    """What the bot managed to do about a spam message."""

    deleted: bool  # False: older than 48 hours, or someone deleted it first
    punished: bool  # muted or banned as the chat is set up; True for "delete only"
    need_right: bool  # punishing failed because the bot lacks the "Ban users" right


def strip_links(text: str) -> str:
    """Drop the words Telegram would turn into links: spammers put their channel into their
    name, and the AI quotes it in its reason."""
    return " ".join(word for word in text.split() if not LINKISH.search(word))


def display_name(sender_id: int, name: str) -> str:
    name = strip_links(name)
    if len(name) > NAME_LIMIT:
        name = name[: NAME_LIMIT - 1] + "…"
    return name or str(sender_id)


def mention(sender_id: int, name: str) -> str:
    """The sender in HTML: a person links to their profile; a channel's title stays plain
    text, as a link would only advertise the spam channel."""
    name = display_name(sender_id, name)
    return escape(name) if is_channel(sender_id) else user_link(sender_id, name)


def punishment_text(t: Ru, action: str, channel: bool, outcome: Outcome) -> str:
    """What the report says happened to the sender: what the chat asked for, or that it failed."""
    if action == Action.DELETE:
        return t.PUNISH_DELETE
    if not outcome.punished:
        failed = t.MUTE_FAILED if action == Action.MUTE and not channel else t.BAN_FAILED
        return failed + (t.NEED_BAN_RIGHT if outcome.need_right else "")
    if channel:
        return t.PUNISH_CHANNEL
    return t.PUNISH_MUTE if action == Action.MUTE else t.PUNISH_BAN


def utf16_len(text: str) -> int:
    return len(text.encode("utf-16-le")) // 2


def cut(text: str, limit: int) -> str:
    """At most `limit` UTF-16 code units, the way Telegram measures a message."""
    if utf16_len(text) <= limit:
        return text
    head = text.encode("utf-16-le")[: 2 * (limit - 1)].decode("utf-16-le", errors="ignore")
    return head + "…"


def restored_text(
    t: Ru, admin_id: int, admin_name: str, user_id: int, user_name: str, text: str
) -> str:
    """The report after a Restore, quoting the removed message as far as it fits."""
    # Measured with the names as shown; the HTML tags in the template count too, as a margin
    frame = t.RESTORED.format(
        admin=display_name(admin_id, admin_name), user=display_name(user_id, user_name), text=""
    )
    quote = cut(text, MESSAGE_LIMIT - utf16_len(frame))
    return t.RESTORED.format(
        admin=mention(admin_id, admin_name), user=mention(user_id, user_name), text=escape(quote)
    )

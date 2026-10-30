"""A link a subscriber sends -> one of their own sources, checked before it is saved."""

import re
from dataclasses import dataclass
from urllib.parse import urlsplit

from jobradar import sources
from jobradar.models import SourceKind

# Telegram usernames: 5-32 letters, digits and underscores, not starting with a digit
TG_NAME = re.compile(r"[A-Za-z][A-Za-z0-9_]{3,31}")
TG_HOSTS = {"t.me", "telegram.me", "www.t.me"}
REDDIT_HOSTS = {"reddit.com", "www.reddit.com", "old.reddit.com", "new.reddit.com"}
SUBREDDIT = re.compile(r"[A-Za-z0-9_]{2,21}")
URL = re.compile(r"https?://\S+|(?:t\.me|telegram\.me|(?:www\.|old\.)?reddit\.com)/\S+", re.I)


@dataclass(frozen=True)
class Link:
    kind: str
    ref: str

    @property
    def key(self) -> str:
        return f"{self.kind}:{self.ref}"

    @property
    def label(self) -> str:
        return label(self.kind, self.ref)


def label(kind: str, ref: str) -> str:
    if kind == SourceKind.TELEGRAM:
        return f"@{ref}"
    if kind == SourceKind.REDDIT:
        return f"r/{ref}"
    return urlsplit(ref).hostname or ref


def looks_like_link(text: str) -> bool:
    text = text.strip()
    return bool(URL.search(text)) or (text.startswith("@") and " " not in text)


def telegram_link(path: list[str]) -> Link | None:
    if path and path[0] == "s":  # the web preview link t.me/s/channel
        path = path[1:]
    # Invite links (t.me/+x, t.me/joinchat/x) and private chats can't be read
    if path and TG_NAME.fullmatch(path[0]) and path[0].lower() != "joinchat":
        return Link(SourceKind.TELEGRAM, path[0].lower())
    return None


def reddit_link(path: list[str]) -> Link | None:
    match path:
        case ["r" | "R", name, *_] if SUBREDDIT.fullmatch(name):
            return Link(SourceKind.REDDIT, name.lower())
    return None


def feed_link(url: str) -> Link | None:
    try:
        sources.check_public_url(url)
    except ValueError:
        return None
    return Link(SourceKind.RSS, url[:512])


def parse(text: str) -> Link | None:
    """Understands t.me/channel, @channel, reddit.com/r/sub and any http(s) feed URL."""
    text = text.strip()
    if text.startswith("@"):
        name = text[1:]
        return Link(SourceKind.TELEGRAM, name.lower()) if TG_NAME.fullmatch(name) else None
    found = URL.search(text)
    if not found:
        return None
    url = found[0].rstrip(".,;)")
    if not url.lower().startswith(("http://", "https://")):
        url = "https://" + url
    parts = urlsplit(url)
    host = (parts.hostname or "").lower()
    path = [p for p in parts.path.split("/") if p]
    if host in TG_HOSTS:
        return telegram_link(path)
    if host in REDDIT_HOSTS:
        return reddit_link(path)
    return feed_link(url)


async def readable(link: Link) -> bool:
    """Fetch the source once: a private channel, an empty subreddit or a page that
    isn't a feed would never give any jobs."""
    if link.kind == SourceKind.TELEGRAM:
        fetch = sources.telegram(link.ref)
    elif link.kind == SourceKind.REDDIT:
        fetch = sources.subreddits([link.ref])
    else:
        fetch = sources.rss(link.ref)
    async with sources.session() as http:
        try:
            return bool(await fetch(http))
        except sources.READ_ERRORS:
            return False

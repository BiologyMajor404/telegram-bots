"""Small HTML helpers for message texts."""

from html import escape


def user_link(user_id: int, name: str) -> str:
    """A clickable mention that works even for people without a @username."""
    return f'<a href="tg://user?id={user_id}">{escape(name)}</a>'

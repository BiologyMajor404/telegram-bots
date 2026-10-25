"""How ChatGuard picks the language: one stored language per group, the user's Telegram
language in private chats."""

from chatguard import repo
from shared.i18n import group_lang_resolver

resolve_lang = group_lang_resolver(repo.ensure_chat)

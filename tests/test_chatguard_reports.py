"""ChatGuard reports: no links from spammers' names or the AI's reason, and texts that fit."""

import pytest

from chatguard.models import Action
from chatguard.reports import (
    MESSAGE_LIMIT,
    NAME_LIMIT,
    Outcome,
    cut,
    display_name,
    mention,
    punishment_text,
    restored_text,
    strip_links,
    utf16_len,
)
from chatguard.texts import TEXTS

EN = TEXTS["en"]
CHANNEL = -1001234567890


@pytest.mark.parametrize(
    ("text", "clean"),
    [
        ("Anna 💰 t.me/+AbCd", "Anna 💰"),
        ("Earn here: https://scam.xyz/x now", "Earn here: now"),
        ("Join @crypto_kings today", "Join today"),
        ("Visit bit.ly/abc or www.site.com", "Visit or"),
        ("Mail me: spam@mail.com", "Mail me:"),
        ("Реклама канала t.me/joinchat/abc с бонусами", "Реклама канала с бонусами"),
        # Ordinary dots stay: abbreviations, numbers, versions
        ("Иван т.е. Ваня, 3.14, v2.0", "Иван т.е. Ваня, 3.14, v2.0"),
    ],
)
def test_strip_links(text, clean):
    assert strip_links(text) == clean


def test_display_name_is_cut_and_never_empty():
    long = display_name(5, "A" * 200)
    assert len(long) == NAME_LIMIT and long.endswith("…")
    assert display_name(5, "t.me/+spam @spam") == "5"


def test_channel_is_named_without_a_link_and_a_person_with_their_profile():
    channel = mention(CHANNEL, "Free <money> t.me/+AbCd")
    assert channel == "Free &lt;money&gt;" and "href" not in channel
    assert mention(5, "Anna @anna_ads") == '<a href="tg://user?id=5">Anna</a>'


DONE = Outcome(deleted=True, punished=True, need_right=False)
FAILED = Outcome(deleted=True, punished=False, need_right=False)
NO_RIGHT = Outcome(deleted=True, punished=False, need_right=True)


@pytest.mark.parametrize(
    ("action", "channel", "outcome", "expected"),
    [
        (Action.DELETE, False, DONE, ""),
        (Action.MUTE, False, DONE, ", they are muted now"),
        (Action.BAN, False, DONE, ", they are banned"),
        (Action.MUTE, True, DONE, ", posting as this channel is blocked here now"),
        (Action.MUTE, False, NO_RIGHT, "; couldn't mute them: give me the “Ban users” right"),
        # The bot has the right (e.g. a basic group can't mute): no misleading advice
        (Action.MUTE, False, FAILED, "; couldn't mute them"),
        (Action.BAN, True, FAILED, "; couldn't ban them"),
    ],
)
def test_punishment_text_says_what_really_happened(action, channel, outcome, expected):
    assert punishment_text(EN, action, channel, outcome) == expected


def test_cut_counts_like_telegram():
    assert cut("short", 10) == "short"
    emoji = "😀" * 10  # two UTF-16 code units each
    assert utf16_len(cut(emoji, 7)) <= 7
    assert cut(emoji, 7) == "😀" * 3 + "…"


MARKUP = ("<blockquote>", "</blockquote>", '<a href="tg://user?id=1">', '<a href="tg://user?id=2">')


@pytest.mark.parametrize("lang", sorted(TEXTS))
def test_restored_message_fits_into_one_telegram_message(lang):
    huge = "<b>&" + "🙂" * 3000 + "x" * 2000  # ~8000 UTF-16 code units
    name = "😀" * 100
    text = restored_text(TEXTS[lang], 1, name, 2, name, huge)
    assert "&lt;b&gt;&amp;" in text  # the quoted message is escaped
    # What Telegram counts: the text without tags, an entity as one character
    visible = text
    for tag in (*MARKUP, "</a>"):
        visible = visible.replace(tag, "")
    visible = visible.replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&")
    assert utf16_len(visible) <= MESSAGE_LIMIT


def test_short_restored_message_is_quoted_whole():
    text = restored_text(EN, 1, "Admin", 2, "Anna", "Hello there")
    assert "<blockquote>Hello there</blockquote>" in text and "…" not in text

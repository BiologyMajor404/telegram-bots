"""Fast, free spam signals. Pure functions: no DB, no Telegram, no AI.

Each signal adds points. A high score is spam without asking the AI, zero is clean,
anything in between is "doubtful" and goes to the AI (or passes if AI is off)."""

import re
from dataclasses import dataclass, field

SPAM_SCORE = 5  # this many points or more: spam by rules alone
# Emoji flood: this many emoji, or this share of a message at least EMOJI_MIN_LENGTH long
EMOJI_MIN_COUNT = 8
EMOJI_MIN_LENGTH = 10
EMOJI_MAX_SHARE = 0.2
# CAPS: more than this share of upper-case letters in a text with enough letters
CAPS_MIN_LETTERS = 20
CAPS_MAX_SHARE = 0.6

LINK_RE = re.compile(
    r"(https?://|www\.|\bt\.me/|\btelegram\.me/|\b[\w-]+\.(?:com|ru|ua|pl|io|xyz|top|site|online|"
    r"shop|link|click|info|biz|net|org)\b)",
    re.I,
)
INVITE_RE = re.compile(r"(t\.me/\+|t\.me/joinchat|telegram\.me/joinchat)", re.I)
MENTION_RE = re.compile(r"(?<![\w@])@[A-Za-z][\w]{4,}")
PHONE_RE = re.compile(r"(?:\+?\d[\s\-()]?){10,}")
EMOJI_RE = re.compile("[\U0001f300-\U0001faff☀-➿]")

# Lower-case stems in uk / ru / pl / en. Matching is by substring, so stems catch word forms.
MONEY_WORDS = [
    # earnings / jobs
    "заработ",
    "заробі",
    "заробіт",
    "доход",
    "дохід",
    "пассивн",
    "пасивн",
    "удалённ",
    "удаленн",
    "віддален",
    "подработ",
    "підробіт",
    "zarob",
    "dochód",
    "praca zdalna",
    "earn",
    "income",
    "passive",
    "remote job",
    "work from home",
    # money amounts / profit
    "$ в день",
    "в день от",
    "на день від",
    "за день",
    "per day",
    "dziennie",
    "profit",
    "прибыл",
    "прибут",
    "zysk",
    # crypto / investing
    "крипт",
    "crypto",
    "kryptowalut",
    "биткоин",
    "біткоїн",
    "bitcoin",
    "usdt",
    "инвест",
    "інвест",
    "invest",
    "трейд",
    "trading",
    "airdrop",
    "forex",
    "форекс",
    # casino / betting
    "казино",
    "casino",
    "kasyno",
    "ставк",
    "betting",
    "бонус",
    "bonus",
]
DM_WORDS = [
    "пиши в лс",
    "пишите в лс",
    "в личку",
    "в лс",
    "пиши в особисті",
    "в особисті",
    "в приват",
    "write me",
    "dm me",
    "text me",
    "pm me",
    "pisz na priv",
    "napisz prywatnie",
    "pisz pw",
]


@dataclass
class RulesVerdict:
    score: int = 0
    reasons: list[str] = field(default_factory=list)

    def add(self, points: int, reason: str) -> None:
        self.score += points
        self.reasons.append(reason)

    @property
    def is_spam(self) -> bool:
        return self.score >= SPAM_SCORE

    @property
    def is_clean(self) -> bool:
        return self.score == 0


def check(
    text: str,
    *,
    forwarded_from_channel: bool = False,
    has_buttons: bool = False,
    has_link_entities: bool = False,
    known_spammer: bool = False,
) -> RulesVerdict:
    v = RulesVerdict()
    low = text.lower()

    if known_spammer:  # caught in another chat (shared list, Pro only)
        v.add(3, "known")

    if INVITE_RE.search(text):
        v.add(3, "invite")
    elif LINK_RE.search(text) or has_link_entities:
        v.add(2, "link")
    if MENTION_RE.search(text):
        v.add(1, "mention")

    money_hits = sum(1 for w in MONEY_WORDS if w in low)
    if money_hits:
        v.add(min(money_hits, 3), "money")
    if any(w in low for w in DM_WORDS):
        v.add(2, "dm")

    if forwarded_from_channel:
        v.add(2, "forward")
    if has_buttons:
        v.add(2, "buttons")
    if PHONE_RE.search(text):
        v.add(1, "phone")

    emojis = len(EMOJI_RE.findall(text))
    if emojis >= EMOJI_MIN_COUNT or (
        len(text) >= EMOJI_MIN_LENGTH and emojis / len(text) > EMOJI_MAX_SHARE
    ):
        v.add(1, "emoji")
    letters = [c for c in text if c.isalpha()]
    upper_share = sum(c.isupper() for c in letters) / len(letters) if letters else 0
    if len(letters) >= CAPS_MIN_LETTERS and upper_share > CAPS_MAX_SHARE:
        v.add(1, "caps")
    return v

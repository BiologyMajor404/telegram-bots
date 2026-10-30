"""Searches in the subscribers' own words: matching posts to them and querying job boards.

A search is a label ("моушн-дизайнер") plus keywords the AI made for it once, in several
languages. Keywords are plain lowercase fragments, so a stem like "монтаж" also finds
"монтажёр" and "відеомонтаж". They only shortlist posts; the AI makes the final call."""

import re
from collections.abc import Iterable, Mapping

LABEL_MIN, LABEL_MAX = 2, 40
KEYWORD_MIN = 3  # shorter fragments would match almost any post
# Up to this length a keyword must be a whole word: "seo" mustn't fire on "seoul"
WHOLE_WORD_MAX = 3
# Hiring subreddits searched with everyone's keywords
REDDIT_SUBS = (
    "forhire",
    "hireavideoeditor",
    "videoeditingrequests",
    "designjobs",
    "hireawriter",
    "hungryartists",
    "jobs4bitcoins",
)
QUERIES_PER_RUN = 15  # per job board, so many searches can't flood the boards with requests


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower().replace("ё", "е")).strip()


def clean_label(text: str) -> str | None:
    """A subscriber's typed search, tidied; None if it can't be one."""
    label = re.sub(r"\s+", " ", text).strip().strip(".,;:!?\"'«»")
    if not LABEL_MIN <= len(label) <= LABEL_MAX or label.startswith("/") or "://" in label:
        return None
    return label


def clean_keywords(label: str, words: Iterable[str]) -> list[str]:
    """The AI's keywords, normalized and deduplicated, with the label itself first."""
    result = [normalize(label)]
    for raw in words:
        word = normalize(str(raw))[:64]
        if len(word) >= KEYWORD_MIN and word not in result:
            result.append(word)
    return result[:20]


def found(word: str, haystack: str) -> bool:
    if len(word) < KEYWORD_MIN:
        # Only a short label like "IT" or "PR" gets here: as a fragment it is in every post,
        # so such a search relies on the AI's longer keywords
        return False
    if len(word) > WHOLE_WORD_MAX:
        return word in haystack  # a stem: "монтаж" also finds "відеомонтаж"
    return re.search(rf"(?<!\w){re.escape(word)}(?!\w)", haystack) is not None


def matching(title: str, text: str, searches: Mapping[str, list[str]]) -> set[str]:
    """Labels whose keywords appear in the post."""
    haystack = normalize(f"{title}\n{text[:3000]}")
    return {label for label, words in searches.items() if any(found(w, haystack) for w in words)}


def board_queries(searches: Mapping[str, list[str]], turn: int = 0) -> list[str]:
    """What to type into job board search boxes: each label and up to two phrases.
    Single-word stems stay out: a board searching "монтаж" returns pipe fitters. When there
    are more than a run may send, each `turn` (run) takes the next ones, so every search
    gets its turn."""
    queries: dict[str, None] = {}
    for label, words in searches.items():
        phrases = [w for w in words if " " in w and w != label]
        # One English phrase too: international boards search in English
        english = next((p for p in phrases if p.isascii()), None)
        for query in [label, *phrases[:2], english]:
            if query:
                queries[query] = None
    listed = list(queries)
    if len(listed) <= QUERIES_PER_RUN:
        return listed
    start = turn * QUERIES_PER_RUN % len(listed)
    return (listed[start:] + listed[:start])[:QUERIES_PER_RUN]

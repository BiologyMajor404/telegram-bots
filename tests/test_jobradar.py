"""JobRadar: the cheap filters before the AI, feed parsing, filters and the job card."""

import time
from datetime import UTC, datetime, timedelta

import anthropic
import pytest

from jobradar.ai import Niche, cost_usd, parse
from jobradar.card import card
from jobradar.filters import mismatch
from jobradar.models import Subscriber
from jobradar.relevance import candidates, searches_in
from jobradar.sources import RawJob, decode, parse_channel, plain, salary_range
from jobradar.texts import TEXTS

NOW = datetime(2026, 10, 28, 12, tzinfo=UTC)
# The owner's search, as moved over from the old fixed "video editor" profession
VIDEO = {
    "видеомонтаж": [
        "видеомонтаж",
        "відеомонтаж",
        "монтажер",
        "монтаж видео",
        "монтаж відео",
        "режисер монтажу",
        "режисер(ка) монтажу",
        "режисерка монтажу",
        "відео монтаж",
        "видео монтаж",
        "video editor",
        "video editing",
        "podcast editor",
        "videoedit",
        "podcast edit",
        "відеоредактор",
        "видеоредактор",
        "reels editor",
        "short-form editor",
        "youtube editor",
        "рилсмейкер",
        "premiere pro",
        "capcut",
        "davinci",
    ]
}
MOTION = {"моушн-дизайнер": ["моушн-дизайнер", "моушн", "motion design", "after effects"]}


def job(title: str, text: str = "", age_hours: int = 1, **kw) -> RawJob:
    return RawJob(
        source=kw.get("source", "test"),
        external_id=kw.get("external_id", title),
        title=title,
        text=text,
        url="https://example.com/job",
        published=NOW - timedelta(hours=age_hours),
    )


@pytest.mark.parametrize(
    "title",
    [
        "Video Editor (Freelance)",
        "[Hiring] Podcast editor for weekly show",
        "Відеомонтажер/відеомонтажерка YouTube-контенту",
        "Відео монтажник",
        "Режисер(ка) монтажу",
        "Видеомонтажер для Reels",
        "Reels-монтажер/Рилсмейкер",
        "Short-form editor (TikTok)",
    ],
)
def test_video_jobs_pass(title):
    assert searches_in(job(title), VIDEO) == set(VIDEO)


@pytest.mark.parametrize(
    "title",
    [
        "Senior Backend Engineer",
        "SMM-менеджер",
        "[For Hire] Video Editor - Reels / TikTok",  # a freelancer offering services
        "#резюме Видеомонтажер, 3 года опыта",
    ],
)
def test_other_posts_are_dropped(title):
    assert not searches_in(job(title), VIDEO)


def test_description_counts_when_title_is_vague():
    vague = job("Content creator", "You will edit in Premiere Pro and CapCut")
    assert searches_in(vague, VIDEO) == set(VIDEO)


def test_each_search_is_matched_on_its_own_words():
    both = VIDEO | MOTION
    assert searches_in(job("Motion Designer (After Effects)"), both) == {"моушн-дизайнер"}
    assert searches_in(job("Моушн-дизайнер / видеомонтажёр"), both) == set(both)
    # ё and case don't matter
    assert searches_in(job("ВИДЕОМОНТАЖЁР"), VIDEO) == set(VIDEO)


def test_short_searches_match_whole_words_only():
    searches = {
        "it": ["it", "it support", "системный администратор"],
        "seo": ["seo", "seo specialist"],
    }
    # "it" alone is in almost every post: a two-letter search lives on its longer keywords
    assert not searches_in(job("Edit our wedding films, it is easy"), searches)
    assert searches_in(job("IT support engineer"), searches) == {"it"}
    assert searches_in(job("SEO-специалист"), searches) == {"seo"}
    assert not searches_in(job("Barista in Seoul"), searches)


def test_employers_asking_for_a_cv_still_pass():
    assert searches_in(job("Шукаємо відеомонтажера, резюме в лс"), VIDEO) == set(VIDEO)


def test_candidates_keep_fresh_unique_oldest_first():
    jobs = [
        job("Video editor A", age_hours=5),
        job("Video editor B", age_hours=1),
        job("Video editor A", age_hours=5),  # the same post from a second query
        job("Video editor old", age_hours=24 * 3),
        job("Accountant", age_hours=1),
    ]
    fresh = candidates(jobs, NOW, VIDEO)
    assert [j.title for j in fresh] == ["Video editor A", "Video editor B"]


def test_plain_is_quick_on_brackets_that_never_close():
    started = time.perf_counter()
    plain("<" * 200_000)
    assert time.perf_counter() - started < 1


def test_unknown_or_slow_charsets_fall_back_to_utf8():
    word = "Вакансія"
    assert decode(word.encode(), "x-bogus") == word
    assert decode(word.encode(), "punycode") == word
    assert decode(word.encode(), "base64") == word
    assert decode("Работа".encode("cp1251"), "windows-1251") == "Работа"
    assert decode(word.encode(), None) == word


def test_plain_strips_html():
    assert plain("<p>Edit <b>podcasts</b> &amp; reels</p><p>Remote</p>") == (
        "Edit podcasts & reels\nRemote"
    )


@pytest.mark.parametrize(
    ("args", "expected"),
    [
        ((20000, 30000, "UAH"), "20000–30000 UAH"),
        ((0, 0, "USD"), ""),
        ((None, 55000, "USD", "year"), "55000 USD year"),
    ],
)
def test_salary_range(args, expected):
    assert salary_range(*args) == expected


CHANNEL_PAGE = """
<div class="tgme_widget_message_wrap js-widget_message_wrap">
  <div class="tgme_widget_message" data-post="jobs_ch/101">
    <div class="tgme_widget_message_text js-message_text" >Видеомонтажер<br/>Удалённо</div>
    <time datetime="2026-10-28T10:00:00+00:00" class="time">10:00</time>
  </div>
</div>
<div class="tgme_widget_message_wrap js-widget_message_wrap">
  <div class="tgme_widget_message" data-post="jobs_ch/102">
    <time datetime="2026-10-28T11:00:00+00:00" class="time">11:00</time>
  </div>
</div>
<div class="tgme_widget_message_wrap js-widget_message_wrap">
  <div class="tgme_widget_message" data-post="jobs_ch/103">
    <div class="tgme_widget_message_text js-message_text">SMM manager</div>
    <time datetime="2026-10-28T12:00:00+00:00" class="time">12:00</time>
  </div>
</div>
"""


def test_parse_channel_skips_posts_without_text():
    jobs = parse_channel(CHANNEL_PAGE)
    assert [j.external_id for j in jobs] == ["jobs_ch/101", "jobs_ch/103"]
    assert jobs[0].title == "Видеомонтажер"
    assert jobs[0].url == "https://t.me/jobs_ch/101"
    assert jobs[0].published == datetime(2026, 10, 28, 10, tzinfo=UTC)


ASKED = ["видеомонтаж", "моушн-дизайнер"]  # the searches shown to the AI with a post
MINE = {"видеомонтаж"}  # the owner's searches
ANSWER = {
    "matches": ["видеомонтаж"],
    "is_offer": True,
    "scam": False,
    "remote": "full",
    "schedule": "unknown",
    "languages": ["en"],
    "employer_region": "us",
    "residency": [],
    "paid": "paid",
    "niche": "podcast",
    "title": "Монтажёр подкастов",
    "duties": "Монтировать <выпуски> подкаста",
    "software": ["Premiere Pro", "Descript"],
    "country": "США",
    "pay": "$25 за выпуск",
    "summary": "Еженедельный подкаст, 2 выпуска в неделю.",
    "translated": True,
}


def facts(**changes):
    return parse(ANSWER | changes, ASKED)


def me(**filters) -> Subscriber:
    """The bot's first user: the defaults the filters start with."""
    base = {
        "remote_only": True,
        "flexible_only": True,
        "languages": ["en", "uk", "ru"],
        "regions": ["us", "eu", "ua"],
        "country": "UA",
    }
    return Subscriber(id=1, lang="ru", **(base | filters))


def test_a_suitable_job_passes_and_unknowns_are_fine():
    assert mismatch(me(), MINE, facts()) is None
    unknown = {"remote": "unknown", "employer_region": "unknown", "paid": "unknown"}
    assert mismatch(me(), MINE, facts(**unknown)) is None


@pytest.mark.parametrize(
    ("changes", "reason"),
    [
        ({"is_offer": False}, "not_offer"),
        ({"scam": True}, "not_offer"),
        ({"paid": "revenue_share"}, "unpaid"),
        ({"matches": ["моушн-дизайнер"]}, "search"),
        ({"matches": []}, "search"),
        ({"remote": "onsite"}, "onsite"),
        ({"remote": "hybrid"}, "onsite"),
        ({"schedule": "fixed"}, "schedule"),
        ({"languages": ["en", "de"]}, "languages"),
        ({"employer_region": "ru_by"}, "region"),
        ({"residency": ["US"]}, "residency"),
    ],
)
def test_jobs_failing_a_filter_are_dropped(changes, reason):
    assert mismatch(me(), MINE, facts(**changes)) == reason


def test_the_ai_can_only_name_searches_it_was_given():
    assert facts(matches=["видеомонтаж", "invented"]).matches == {"видеомонтаж"}


def test_filters_can_be_loosened():
    hybrid_fixed = facts(remote="hybrid", schedule="fixed")
    assert mismatch(me(remote_only=False, flexible_only=False), MINE, hybrid_fixed) is None
    german = facts(languages=["de"])
    assert mismatch(me(languages=["en", "de"]), MINE, german) is None


def test_a_combined_role_reaches_both_searches():
    both = facts(matches=["моушн-дизайнер", "видеомонтаж"])
    assert mismatch(me(), {"видеомонтаж"}, both) is None
    assert mismatch(me(), {"моушн-дизайнер"}, both) is None


def test_eu_residency_counts_for_every_eu_country():
    eu_only = facts(residency=["EU"])
    assert mismatch(me(country="PL"), MINE, eu_only) is None
    assert mismatch(me(country="UA"), MINE, eu_only) == "residency"


def test_cost_counts_cache_and_output_tokens():
    usage = anthropic.types.Usage(
        input_tokens=1_000_000,
        output_tokens=1_000_000,
        cache_creation_input_tokens=1_000_000,
        cache_read_input_tokens=1_000_000,
    )
    # 0.10 input + 0.125 cache write + 0.01 cache read + 0.50 output
    assert cost_usd(usage) == pytest.approx(0.735)


def test_parse_falls_back_to_other_for_unknown_niche():
    assert facts(niche="cooking").niche == Niche.OTHER


def test_card_escapes_and_marks_top_jobs():
    text = card(job("Podcast editor"), facts(), TEXTS["ru"], ["Видеомонтаж"])
    assert text.startswith("🔥 <b>Монтажёр подкастов</b>")
    assert "<i>Видеомонтаж · Подкаст</i>" in text
    assert "&lt;выпуски&gt;" in text  # AI output is escaped, it can't inject HTML
    assert "Перевод:" in text
    assert "$25 за выпуск" in text


def test_card_shows_the_readers_own_search_names():
    a = facts(matches=["моушн-дизайнер"], niche="other")
    text = card(job("Motion"), a, TEXTS["en"], ["Моушн <дизайн>"])
    assert text.startswith("💼")
    assert "<i>Моушн &lt;дизайн&gt;</i>" in text  # the user's own text is escaped too


def test_card_says_not_stated_for_missing_pay():
    a = facts(niche="wedding", pay="", software=[], translated=False)
    text = card(job("Wedding editor"), a, TEXTS["en"], ["Video editing"])
    assert text.startswith("🎬")
    assert "Pay:</b> not stated" in text
    assert "Software:</b> not stated" in text
    assert "In short:" in text

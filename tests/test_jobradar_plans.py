"""JobRadar: own sources by link, feed parsing, and who gets a job under the Free/Pro limits."""

import xml.etree.ElementTree as ET
from datetime import UTC, date, datetime, timedelta

import pytest

from jobradar import links
from jobradar.config import Plan, Plans
from jobradar.handlers.filters import filters_text, toggle
from jobradar.handlers.payments import already_pro
from jobradar.handlers.private import plan_text
from jobradar.models import SourceKind, Subscriber, UserDay, UserSearch
from jobradar.plans import Access, recipients, within_plans
from jobradar.searches import board_queries, clean_keywords, clean_label
from jobradar.sources import (
    check_public_url,
    global_feeds,
    global_keys,
    parse_feed,
    parse_freelancehunt,
    user_feeds,
)
from jobradar.texts import TEXTS

NOW = datetime(2026, 10, 28, 12, tzinfo=UTC)
TODAY = date(2026, 10, 28)
PLANS = Plans(
    free=Plan(cards=5, sources=1, searches=3, own_checks=15),
    pro=Plan(cards=20, sources=10, searches=10, own_checks=60),
    pro_price_stars=250,
    base_usd=3.0,
    usd_per_pro=2.5,
)
ADMIN = 1
ACCESS = Access(PLANS, admin_ids={ADMIN})
GLOBAL = global_keys(["theyseeku"])


@pytest.mark.parametrize(
    ("text", "kind", "ref"),
    [
        ("https://t.me/Video_Jobs", SourceKind.TELEGRAM, "video_jobs"),
        ("t.me/s/video_jobs", SourceKind.TELEGRAM, "video_jobs"),
        ("look at https://t.me/video_jobs/123 please", SourceKind.TELEGRAM, "video_jobs"),
        ("@video_jobs", SourceKind.TELEGRAM, "video_jobs"),
        ("https://www.reddit.com/r/VideoEditing/", SourceKind.REDDIT, "videoediting"),
        ("old.reddit.com/r/forhire/new", SourceKind.REDDIT, "forhire"),
        ("https://example.com/jobs.rss", SourceKind.RSS, "https://example.com/jobs.rss"),
    ],
)
def test_links_are_understood(text, kind, ref):
    link = links.parse(text)
    assert (link.kind, link.ref) == (kind, ref)


@pytest.mark.parametrize(
    "text",
    [
        "https://t.me/+AbCdEf",  # private invite
        "https://t.me/joinchat/AbCdEf",
        "https://t.me/c/123/45",  # private chat
        "https://reddit.com/user/someone",
        "http://localhost/feed",
        "http://127.0.0.1/feed",
        "http://10.0.0.5/feed",
        "http://169.254.169.254/latest/meta-data",  # cloud metadata
        "http://[::1]/feed",
        "http://１２７.０.０.１/feed",  # fullwidth 127.0.0.1
        "http://127.1/feed",
        "http://0177.0.0.1/feed",
        "http://0x7f.0.0.1/feed",
        "https://example.com:8080/feed",
        "ftp://example.com/feed",
        "just some words",
    ],
)
def test_unusable_links_are_refused(text):
    assert links.parse(text) is None


def test_internal_hosts_are_refused():
    for url in ("http://postgres:5432/", "http://redis/", "http://0.0.0.0/"):
        with pytest.raises(ValueError):
            check_public_url(url)
    check_public_url("https://example.com/feed")  # a public host passes; DNS is checked later


RSS = """<?xml version="1.0"?>
<rss version="2.0"><channel><title>Jobs</title>
  <item><title>Video editor &amp; colorist</title><link>https://ex.com/1</link>
    <guid>job-1</guid><description>&lt;p&gt;Edit &lt;b&gt;podcasts&lt;/b&gt;&lt;/p&gt;</description>
    <pubDate>Wed, 28 Oct 2026 10:00:00 GMT</pubDate></item>
  <item><title>No link</title></item>
</channel></rss>"""

ATOM = """<?xml version="1.0"?>
<feed xmlns="http://www.w3.org/2005/Atom"><title>Jobs</title>
  <entry><id>tag:ex.com,1</id><title>Reels editor</title>
    <link href="https://ex.com/a"/><summary>Short-form</summary>
    <updated>2026-10-28T09:00:00Z</updated></entry>
</feed>"""


def test_rss_feed():
    [job] = parse_feed(RSS, "https://ex.com/feed")
    assert job.title == "Video editor & colorist"
    assert job.text == "Edit podcasts"
    assert job.external_id == "job-1"
    assert job.published == datetime(2026, 10, 28, 10, tzinfo=UTC)
    assert job.feed == "rss:https://ex.com/feed"
    assert job.source == "ex.com"


def test_atom_feed():
    [job] = parse_feed(ATOM, "https://ex.com/atom")
    assert (job.title, job.url, job.text) == ("Reels editor", "https://ex.com/a", "Short-form")
    assert job.published == datetime(2026, 10, 28, 9, tzinfo=UTC)


def test_a_web_page_is_not_a_feed():
    with pytest.raises(Exception):  # noqa: B017 - any parse error will do
        parse_feed("<html><body>Hello</body></html>", "https://ex.com")


def test_feeds_with_entity_declarations_are_refused():
    bomb = '<?xml version="1.0"?><!DOCTYPE r [<!ENTITY a "aaaa">]><rss><channel/></rss>'
    with pytest.raises(ET.ParseError):
        parse_feed(bomb, "https://ex.com/feed")


def test_own_feeds_skip_shared_ones_and_group_subreddits():
    feeds = user_feeds(
        [("tg", "theyseeku"), ("tg", "my_channel"), ("reddit", "a"), ("reddit", "b")],
        skip=GLOBAL,
    )
    assert [f.name for f in feeds] == ["own subreddits", "@my_channel"]


def sub(user_id: int, pro: bool = False) -> Subscriber:
    return Subscriber(
        id=user_id,
        lang="ru",
        active=True,
        only_top=False,
        pro_until=NOW + timedelta(days=3) if pro else None,
    )


def day(user_id: int, cards: int = 0, checks: int = 0) -> UserDay:
    return UserDay(user_id=user_id, day=TODAY, cards=cards, checks=checks)


VIDEO = "видеомонтаж"


def who(feed, subs, own=None, used=None, matched=(VIDEO,), searches=None) -> list[int]:
    searches = searches or {s.id: {VIDEO} for s in subs}
    return [
        s.id
        for s in recipients(
            feed, set(matched), subs, searches, GLOBAL, own or {}, used or {}, ACCESS, NOW
        )
    ]


def test_shared_jobs_go_to_everyone_with_room_left():
    subs = [sub(2), sub(3), sub(4, pro=True)]
    used = {2: day(2, cards=5), 4: day(4, cards=5)}  # 2 is at the Free limit, 4 is Pro
    assert who("tg:theyseeku", subs, used=used) == [3, 4]


def test_jobs_go_only_to_people_with_a_matching_search():
    subs = [sub(2), sub(3), sub(4)]
    searches = {2: {VIDEO}, 3: {"копирайтер"}, 4: {"smm", "копирайтер"}}
    assert who("tg:theyseeku", subs, matched=["копирайтер"], searches=searches) == [3, 4]
    assert who("tg:theyseeku", subs, matched=[VIDEO, "smm"], searches=searches) == [2, 4]


def test_nobody_without_searches_gets_jobs():
    assert who("tg:theyseeku", [sub(2)], searches={2: set()}) == []


def test_own_source_jobs_go_only_to_whoever_added_it():
    subs = [sub(2), sub(3)]
    own = {3: {"tg:my_channel"}}
    assert who("tg:my_channel", subs, own=own) == [3]


def test_own_checks_are_capped_per_plan():
    subs = [sub(2), sub(3, pro=True)]
    own = {2: {"tg:noisy"}, 3: {"tg:noisy"}}
    used = {2: day(2, checks=15), 3: day(3, checks=15)}
    assert who("tg:noisy", subs, own=own, used=used) == [3]


def test_admin_gets_pro_without_paying():
    assert ACCESS.is_pro(sub(ADMIN), NOW)
    assert ACCESS.plan(sub(ADMIN), NOW) == PLANS.pro
    assert ACCESS.plan(sub(2), NOW) == PLANS.free


def test_expired_pro_is_free():
    expired = sub(2)
    expired.pro_until = NOW - timedelta(seconds=1)
    assert not ACCESS.is_pro(expired, NOW)


def test_each_paying_subscriber_adds_to_the_budget():
    assert ACCESS.monthly_usd(0) == 3.0
    assert ACCESS.monthly_usd(4) == pytest.approx(13.0)


@pytest.mark.parametrize(
    ("typed", "label"),
    [
        ("  моушн   дизайнер ", "моушн дизайнер"),
        ("«3D artist».", "3D artist"),
        ("x", None),
        ("/status", None),
        ("https://t.me/x", None),
        ("a" * 41, None),
    ],
)
def test_typed_searches_are_tidied(typed, label):
    assert clean_label(typed) == label


def test_ai_keywords_are_cleaned_with_the_label_first():
    words = clean_keywords("Моушн-дизайнер", ["Motion Designer", "моушн", "ae", "МОУШН", 42])
    assert words == ["моушн-дизайнер", "motion designer", "моушн"]


def test_board_queries_skip_single_word_stems():
    searches = {
        "видеомонтаж": ["видеомонтаж", "монтаж", "монтаж видео", "монтаж відео", "video edit"],
        "smm": ["smm", "social media manager"],
    }
    assert board_queries(searches) == [
        "видеомонтаж",
        "монтаж видео",
        "монтаж відео",
        "video edit",  # the English one, for international boards
        "smm",
        "social media manager",
    ]


def test_board_queries_take_turns_when_there_are_many():
    searches = {f"job{i}": [f"job{i}"] for i in range(20)}
    first, second = board_queries(searches, turn=0), board_queries(searches, turn=1)
    assert len(first) == len(second) == 15
    assert set(first) | set(second) == set(searches)


def test_board_queries_keep_phrases_when_the_label_is_not_first():
    # Searches moved over from the old professions don't start with their label
    searches = {"графический дизайн": ["graphic design", "графический дизайн", "дизайнер"]}
    assert board_queries(searches) == ["графический дизайн", "graphic design"]


def test_filter_taps():
    me = Subscriber(
        id=5,
        remote_only=True,
        flexible_only=True,
        languages=["en"],
        regions=["us", "eu", "ua"],
        country="UA",
    )
    assert not toggle(me, "lang", "en")  # the last one stays
    assert toggle(me, "lang", "pl")
    assert me.languages == ["en", "pl"]
    assert toggle(me, "main", "remote")
    assert me.remote_only is False
    assert toggle(me, "country", "PL")
    assert me.country == "PL"
    toggle(me, "country", "Mars")  # not on the list: ignored
    assert me.country == "PL"


def test_filters_screen_lists_choices_in_the_users_language():
    me = Subscriber(
        remote_only=False,
        flexible_only=True,
        languages=["en", "pl"],
        regions=["eu"],
        country="PL",
    )
    mine = [UserSearch(label="Моушн <дизайн>", keywords=[]), UserSearch(label="SMM", keywords=[])]
    text = filters_text(TEXTS["en"], me, mine)
    assert "Looking for: Моушн &lt;дизайн&gt;, SMM" in text
    assert "remote or hybrid" in text
    assert "English, Polish" in text
    assert "🇵🇱 Poland" in text
    assert "Looking for: nothing yet" in filters_text(TEXTS["en"], me, [])


def test_a_gift_is_pro_without_an_end_date_or_a_payment():
    gifted = sub(7)
    gifted.gift = True
    assert ACCESS.is_pro(gifted, NOW)
    assert plan_text(TEXTS["ru"], gifted, ACCESS) == "⭐ Pro (подарок, бессрочно)"


def test_a_gift_and_a_paid_pro_dont_overwrite_each_other():
    both = sub(7, pro=True)
    both.gift = False  # the gift taken back: the paid month stays
    assert ACCESS.is_pro(both, NOW)
    both.pro_until = None  # the paid month over: a gift alone still counts
    both.gift = True
    assert ACCESS.is_pro(both, NOW)


def test_paying_again_for_a_running_pro_is_refused():
    assert not already_pro(sub(2), NOW)
    assert already_pro(sub(2, pro=True), NOW)  # 3 days left: an old offer's link
    ending = sub(2)
    ending.pro_until = NOW + timedelta(hours=2)  # a renewal comes at the very end
    assert not already_pro(ending, NOW)
    gifted = sub(2)
    gifted.gift = True
    assert already_pro(gifted, NOW)


def test_a_missing_usage_row_counts_as_nothing_used():
    closed = Access(
        Plans(
            free=Plan(cards=0, sources=1, searches=3, own_checks=0),
            pro=PLANS.pro,
            pro_price_stars=250,
            base_usd=3.0,
            usd_per_pro=2.5,
        ),
        admin_ids=set(),
    )
    # With a limit of 0 even the day's first card mustn't go out
    found = recipients("tg:theyseeku", {VIDEO}, [sub(2)], {2: {VIDEO}}, GLOBAL, {}, {}, closed, NOW)
    assert found == []


def test_after_pro_ends_only_what_the_free_plan_allows_works():
    lapsed, pro = sub(2), sub(3, pro=True)
    sources = {2: ["tg:a", "tg:b", "tg:c"], 3: ["tg:a", "tg:b", "tg:c"]}
    searches = [
        UserSearch(user_id=uid, label=label, keywords=[label])
        for uid in (2, 3)
        for label in ("smm", "seo", "ppc", "copywriter")
    ]
    own, kept = within_plans([lapsed, pro], sources, searches, ACCESS, NOW)
    assert own == {2: {"tg:a"}, 3: {"tg:a", "tg:b", "tg:c"}}  # the oldest one stays
    assert [s.label for s in kept if s.user_id == 2] == ["smm", "seo", "ppc"]
    assert len([s for s in kept if s.user_id == 3]) == 4


FREELANCEHUNT = {
    "data": [
        {
            "id": 1661854,
            "attributes": {
                "name": "Монтаж",
                "description_html": "<p>Смонтировать видео</p>",
                "skills": [{"name": "Audio & Video Editing"}],
                "budget": {"amount": 50, "currency": "EUR"},
                "is_remote_job": True,
                "location": None,
                "published_at": "2026-10-29T23:02:17+02:00",
            },
            "links": {"self": {"web": "https://freelancehunt.com/project/montazh/1661854.html"}},
        }
    ]
}


def test_freelancehunt_projects():
    [job] = parse_freelancehunt(FREELANCEHUNT)
    assert (job.title, job.salary, job.location) == ("Монтаж", "50 EUR", "remote")
    assert job.text == "Смонтировать видео\nSkills: Audio & Video Editing"
    assert job.feed == "board:freelancehunt"
    assert job.url.endswith("1661854.html")


def test_freelancehunt_is_off_without_a_token():
    names = [f.name for f in global_feeds(["ch"], ["video editor"])]
    assert "Freelancehunt" not in names
    assert {"DOU", "Djinni", "We Work Remotely"} <= set(names)
    assert "Freelancehunt" in [f.name for f in global_feeds(["ch"], [], "token")]


def test_feed_regions_reach_the_ai():
    page = RSS.replace("<guid>job-1</guid>", "<guid>job-1</guid><region>USA Only</region>")
    [job] = parse_feed(page, "https://ex.com/feed")
    assert job.location == "USA Only"

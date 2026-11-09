"""JobRadar's run loop: Pro subscribers' jobs first, skipped jobs don't use up a run, and
letters to the box's own address are a source for everyone."""

import asyncio
import contextlib
from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

import pytest

from jobradar import radar as radar_module
from jobradar import repo
from jobradar.ai import LetterJob
from jobradar.config import Plan, Plans
from jobradar.mail import SHARED_FEED, Letter, MailConfig
from jobradar.models import Subscriber, UserDay, UserSearch
from jobradar.plans import Access, recipients
from jobradar.radar import PER_RUN, Outcome, Radar, Wanted
from jobradar.sources import RawJob

NOW = datetime(2026, 10, 30, 12, tzinfo=UTC)
PLANS = Plans(
    free=Plan(cards=5, sources=1, searches=3, own_checks=15),
    pro=Plan(cards=20, sources=10, searches=10, own_checks=60),
    pro_price_stars=250,
    base_usd=3.0,
    usd_per_pro=2.5,
)
ACCESS = Access(PLANS, admin_ids=set())
FREE, PRO = 2, 3


def subscriber(user_id: int, pro: bool) -> Subscriber:
    until = NOW + timedelta(days=10) if pro else None
    return Subscriber(id=user_id, lang="ru", active=True, only_top=False, pro_until=until)


def job(name: str, feed: str, age_hours: int) -> RawJob:
    return RawJob(
        source="test",
        external_id=name,
        title="SMM manager",
        text="",
        url=f"https://ex.com/{name}",
        published=NOW - timedelta(hours=age_hours),
        feed=feed,
    )


def run(outcomes: dict[str, Outcome], jobs: list[RawJob]) -> list[str]:
    """Which jobs the loop handed to the AI, in order."""
    radar = Radar(None, None, None, [], ACCESS, 400, ZoneInfo("UTC"))
    radar.wanted = Wanted.of(
        [UserSearch(user_id=uid, label="smm", keywords=["smm"]) for uid in (FREE, PRO)]
    )
    tried: list[str] = []

    async def process(http, job, to, monthly, now):
        tried.append(job.external_id)
        return outcomes.get(job.external_id, Outcome.CHECKED)

    async def nothing_used():
        return {}

    async def monthly_usd():
        return 3.0

    radar._process = process
    radar._usage = nothing_used
    radar.monthly_usd = monthly_usd
    own = {FREE: {"tg:free_own"}, PRO: {"tg:pro_own"}}
    subs = [subscriber(FREE, pro=False), subscriber(PRO, pro=True)]
    asyncio.run(radar._check_all(None, jobs, subs, own, NOW))
    return tried


def test_jobs_a_pro_subscriber_waits_for_go_first():
    older = [job(f"free-{i}", "tg:free_own", age_hours=10 - i) for i in range(3)]
    newer = job("pro", "tg:pro_own", age_hours=1)
    assert run({}, [*older, newer])[0] == "pro"


def test_skipped_jobs_dont_use_up_the_run():
    # Today's free share is spent: free-only jobs are skipped, and after the first one
    # the rest aren't even tried, while Pro jobs still get their checks
    free_only = [job(f"free-{i}", "tg:free_own", age_hours=20 - i) for i in range(12)]
    pro_jobs = [job(f"pro-{i}", "tg:pro_own", age_hours=5 - i) for i in range(3)]
    skips = {j.external_id: Outcome.SKIPPED for j in free_only}
    assert run(skips, [*free_only, *pro_jobs]) == ["pro-0", "pro-1", "pro-2", "free-0"]


def test_a_run_checks_at_most_per_run_jobs():
    many = [job(f"free-{i}", "tg:free_own", age_hours=30 - i) for i in range(PER_RUN + 5)]
    assert len(run({}, many)) == PER_RUN


# --- Letters to the box's own address ---

OWNER = 7
BOX = MailConfig("imap.gmail.com", "jobradar.inbox@gmail.com", "pw", ("pracuj.pl",))
OFFER = LetterJob("Montażysta wideo", "https://www.pracuj.pl/praca/1", "Zlecenie, zdalnie")


def shared_letter(
    sender="mail.pracuj.pl",
    verified=True,
    subject="Nowe oferty",
    links=(),
    text="Montażysta wideo, zlecenie zdalne",
):
    return Letter(None, sender, subject, NOW, text, list(links), verified)


class Mailroom:
    """A radar with fakes around it: what the AI was asked and what the owners were told."""

    def __init__(self, monkeypatch, budget: bool = True) -> None:
        self.read, self.told = 0, []
        owners = Access(PLANS, admin_ids={OWNER})
        self.radar = Radar(None, no_db, self, [], owners, 400, ZoneInfo("UTC"), mail=BOX)
        search = UserSearch(user_id=FREE, label="видеомонтаж", keywords=["montaż", "video editor"])
        self.radar.wanted = Wanted.of([search])

        async def take_check(pro):
            return budget

        async def nothing(*args, **kwargs):
            return None

        async def owner(session, user_id):
            return Subscriber(id=user_id, lang="en")

        async def send(bot, chat_id, text, **kwargs):
            self.told.append((chat_id, text))
            return True

        self.radar.take_check = take_check
        monkeypatch.setattr(repo, "add_ai_cost", nothing)
        monkeypatch.setattr(repo, "get_subscriber", owner)
        monkeypatch.setattr(radar_module, "safe_send", send)

    async def read_letter(self, subject, text, links):
        self.read += 1
        return [OFFER], 0.001

    def letter(self, letter: Letter) -> list[RawJob]:
        return asyncio.run(self.radar._letter(letter, {}, NOW))


@contextlib.asynccontextmanager
async def no_db():
    yield None


def test_a_listed_sites_alert_is_a_source_for_everyone(monkeypatch):
    room = Mailroom(monkeypatch)
    [found] = room.letter(shared_letter())
    assert (found.feed, found.source, found.url) == (SHARED_FEED, "📬 pracuj.pl", OFFER.url)
    assert room.radar.shared_today().jobs == 1
    # /mail names the sites whose alerts keep coming
    assert room.radar.shared_sites(NOW) == ["pracuj.pl"]
    assert room.radar.shared_sites(NOW + timedelta(days=8)) == []
    # Everyone whose search it matches may get it, without spending their own checks
    sub = subscriber(FREE, pro=False)
    used = {FREE: UserDay(user_id=FREE, cards=0, checks=PLANS.free.own_checks)}
    keys = room.radar.global_keys
    assert recipients(SHARED_FEED, {"smm"}, [sub], {FREE: {"smm"}}, keys, {}, used, ACCESS, NOW)


@pytest.mark.parametrize(
    ("sender", "verified", "told"),
    [
        ("evil.example", True, "isn't in JOBRADAR_MAIL_SENDERS"),
        ("pracuj.pl", False, "may be a fake"),
        ("spam.example", False, None),  # neither listed nor genuine: spam, only logged
    ],
)
def test_other_letters_to_the_box_are_not_read(monkeypatch, sender, verified, told):
    room = Mailroom(monkeypatch)
    assert room.letter(shared_letter(sender, verified)) == []
    assert room.letter(shared_letter(sender, verified)) == []
    assert room.read == 0
    # The owners hear about a sender once, and in their own language
    assert [told in text for _, text in room.told] == ([True] if told else [])


def test_a_subscription_confirmation_goes_to_the_owners(monkeypatch):
    room = Mailroom(monkeypatch)
    confirm = ("https://www.pracuj.pl/alerts/confirm?t=a&b=1", "Potwierdzam")
    assert room.letter(shared_letter(subject="Potwierdź subskrypcję", links=[confirm])) == []
    assert room.read == 0
    [(chat_id, text)] = room.told
    assert chat_id == OWNER
    assert "https://www.pracuj.pl/alerts/confirm?t=a&amp;b=1" in text


def test_gmail_forwarding_to_the_box_itself_is_confirmed_by_the_owners(monkeypatch):
    # An owner forwards the alerts of their own account to the box instead of a second one
    room = Mailroom(monkeypatch)
    link = ("https://mail-settings.google.com/mail/vf-abc", "confirm")
    subject = "(#123456789) Gmail Forwarding Confirmation - Receive Mail from me@gmail.com"
    letter = shared_letter("google.com", verified=False, subject=subject, links=[link])
    assert room.letter(letter) == []
    [(chat_id, text)] = room.told
    assert chat_id == OWNER
    assert "<code>123456789</code>" in text


def test_a_letter_about_nobodys_search_isnt_paid_for(monkeypatch):
    # A broad alert (every remote job) mostly names work nobody here looks for
    room = Mailroom(monkeypatch)
    assert room.letter(shared_letter(text="Księgowa, umowa o pracę")) == []
    assert room.read == 0
    assert room.radar.shared_today().letters == 1


def test_a_personal_letter_is_read_only_for_its_readers_own_searches(monkeypatch):
    room = Mailroom(monkeypatch)
    reader = subscriber(FREE, pro=False)

    async def by_token(session, token):
        return reader

    monkeypatch.setattr(repo, "by_mail_token", by_token)
    letter = Letter("0a1b2c3d4e", "upwork.com", "New jobs", NOW, "Accountant needed", [])
    assert asyncio.run(room.radar._letter(letter, {FREE: reader}, NOW)) == []
    assert room.read == 0


def test_a_letter_waits_while_the_budget_is_spent(monkeypatch):
    room = Mailroom(monkeypatch, budget=False)
    letter = shared_letter()
    assert room.letter(letter) == []
    assert room.read == 0
    assert room.radar.unread == [letter]

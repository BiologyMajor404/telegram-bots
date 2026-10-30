"""JobRadar's run loop: Pro subscribers' jobs first, and skipped jobs don't use up a run."""

import asyncio
from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

from jobradar.config import Plan, Plans
from jobradar.models import Subscriber, UserSearch
from jobradar.plans import Access
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

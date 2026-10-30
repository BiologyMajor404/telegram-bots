"""The search loop: read every source, keep fresh jobs matching someone's searches, let the
AI judge the new ones and send the suitable ones to the subscribers whose plan still has
room today."""

import asyncio
import calendar
import contextlib
import hashlib
import imaplib
import logging
from dataclasses import dataclass
from datetime import UTC, date, datetime
from enum import Enum, auto
from html import escape
from zoneinfo import ZoneInfo

import aiohttp
from aiogram import Bot
from sqlalchemy.ext.asyncio import async_sessionmaker

from jobradar import repo, sources
from jobradar.ai import Analysis, Analyzer
from jobradar.card import card
from jobradar.filters import mismatch
from jobradar.keyboards import open_job
from jobradar.mail import Letter, MailConfig, fetch_unseen, gmail_confirmation, read_letter
from jobradar.models import Subscriber, UserDay, UserSearch
from jobradar.plans import Access, recipients, within_plans
from jobradar.relevance import MAX_AGE, candidates, searches_in
from jobradar.searches import board_queries, normalize
from jobradar.texts import TEXTS
from shared.notify import safe_send

log = logging.getLogger(__name__)

# Jobs checked by the AI per run: a burst is spread over several runs instead of one flood
PER_RUN = 8
# Seconds between runs at least, however often something wakes the radar (e.g. /start)
MIN_GAP = 60
# Runs in a row the AI may fail on one post before it is put aside for good
AI_TRIES = 3
UNREAD_MAX = 200  # letters kept for later when their reader's checks are used up


class Outcome(Enum):
    CHECKED = auto()  # the AI was asked
    SKIPPED = auto()  # not now: today's free share of the budget is spent
    STOP = auto()  # nothing more can be checked today


@dataclass(frozen=True)
class Wanted:
    """Everyone's searches for one run, by normalized label."""

    keywords: dict[str, list[str]]  # label -> keywords, merged over subscribers
    labels: dict[int, dict[str, str]]  # subscriber -> {label: label as they typed it}

    @classmethod
    def of(cls, searches: list[UserSearch]) -> "Wanted":
        keywords: dict[str, list[str]] = {}
        labels: dict[int, dict[str, str]] = {}
        for s in searches:
            key = normalize(s.label)
            keywords[key] = list(dict.fromkeys(keywords.get(key, []) + s.keywords))
            labels.setdefault(s.user_id, {})[key] = s.label
        return cls(keywords, labels)

    def keys_of(self) -> dict[int, set[str]]:
        return {user_id: set(found) for user_id, found in self.labels.items()}

    def labels_for(self, user_id: int, matches: frozenset[str]) -> list[str]:
        return [label for key, label in self.labels.get(user_id, {}).items() if key in matches]


@dataclass
class RunStats:
    at: datetime | None = None
    found: int = 0
    fresh: int = 0


class Radar:
    def __init__(
        self,
        bot: Bot,
        session_factory: async_sessionmaker,
        analyzer: Analyzer,
        channels: list[str],
        access: Access,
        ai_daily_limit: int,
        tz: ZoneInfo,
        freelancehunt_token: str = "",
        mail: MailConfig | None = None,
    ) -> None:
        self.bot = bot
        self.session_factory = session_factory
        self.analyzer = analyzer
        self.channels = channels
        self.freelancehunt_token = freelancehunt_token
        self.mail = mail or MailConfig("", "", "")
        self.global_keys = sources.global_keys(channels)
        self.access = access
        self.ai_daily_limit = ai_daily_limit
        self.tz = tz
        self.last = RunStats()
        self.wanted = Wanted({}, {})
        # A letter is read from the box only once: what it gave waits here until checked
        self.letters: list[sources.RawJob] = []
        self.unread: list[Letter] = []  # letters whose reader had no checks left
        self.failures: dict[tuple[str, str], int] = {}  # job -> AI failures so far
        self.turn = 0  # runs so far: job board queries take turns
        self._wake = asyncio.Event()

    def today(self) -> date:
        return datetime.now(self.tz).date()

    def days_in_month(self) -> int:
        today = self.today()
        return calendar.monthrange(today.year, today.month)[1]

    async def monthly_usd(self) -> float:
        async with self.session_factory() as session:
            paying = await repo.paying_count(session, datetime.now(UTC))
        return self.access.monthly_usd(paying)

    async def spent(self) -> tuple[float, float]:
        """USD spent on the AI today and this month."""
        today = self.today()
        async with self.session_factory() as session:
            return (
                await repo.ai_spent(session, today, today),
                await repo.ai_spent(session, today.replace(day=1), today),
            )

    async def take_check(self, pro: bool) -> bool:
        """One AI check for a subscriber's own request (e.g. keywords for a new search),
        if today's budget and check limit still allow it."""
        if await self._within_budget(await self.monthly_usd(), pro) is not True:
            return False
        async with self.session_factory() as session:
            return await repo.reserve_ai_check(session, self.today(), self.ai_daily_limit)

    def wake(self) -> None:
        """Search now instead of at the next tick, e.g. for a new subscriber or source."""
        self._wake.set()

    async def run_forever(self, every_minutes: int) -> None:
        while True:
            self._wake.clear()
            try:
                await self.run_once()
            except Exception:
                log.exception("Search run failed")
            # A pause even when woken right away: job boards and Reddit don't like a
            # stream of requests
            await asyncio.sleep(MIN_GAP)
            with contextlib.suppress(TimeoutError):
                await asyncio.wait_for(self._wake.wait(), max(every_minutes * 60 - MIN_GAP, 0))

    async def run_once(self) -> None:
        now = datetime.now(UTC)
        async with self.session_factory() as session:
            subs = await repo.active_subscribers(session)
            ids = [s.id for s in subs]
            own, searches = within_plans(
                subs,
                await repo.sources_of(session, ids),
                await repo.searches_of(session, ids),
                self.access,
                now,
            )
        self.wanted = Wanted.of(searches)
        subs = [s for s in subs if s.id in self.wanted.labels]
        if not subs:
            return  # nobody to send to: don't spend AI checks
        if self.mail.enabled:
            self.letters += await self._read_mail(subs, now)
        for job in self.letters:  # a letter is its addressee's own source
            own.setdefault(int(job.feed.removeprefix("mail:")), set()).add(job.feed)
        pairs = [key.split(":", 1) for keys in own.values() for key in keys]
        queries = board_queries(self.wanted.keywords, self.turn)
        self.turn += 1
        feeds = sources.global_feeds(
            self.channels, queries, self.freelancehunt_token
        ) + sources.user_feeds(pairs, skip=self.global_keys)
        async with sources.session() as http:
            found = await sources.fetch_all(http, feeds) + self.letters
            fresh = candidates(found, now, self.wanted.keywords)
            async with self.session_factory() as session:
                new = await repo.unseen(session, fresh)
            waiting = set(new)
            self.letters = [job for job in self.letters if job in waiting]
            self.last = RunStats(at=now, found=len(found), fresh=len(fresh))
            log.info("Found %d posts, %d fresh, %d new", len(found), len(fresh), len(new))
            await self._check_all(http, new, subs, own, now)

    async def _check_all(
        self,
        http: aiohttp.ClientSession,
        new: list[sources.RawJob],
        subs: list[Subscriber],
        own: dict[int, set[str]],
        now: datetime,
    ) -> None:
        """Let the AI read the new jobs that have someone to go to: first those a Pro
        subscriber waits for, as the Pro offer promises, then the rest, oldest first."""
        monthly = await self.monthly_usd()
        keys = self.wanted.keys_of()

        def waiting(job: sources.RawJob, used: dict[int, UserDay]) -> list[Subscriber]:
            matched = searches_in(job, self.wanted.keywords)
            return recipients(
                job.feed, matched, subs, keys, self.global_keys, own, used, self.access, now
            )

        def any_pro(to: list[Subscriber]) -> bool:
            return any(self.access.is_pro(s, now) for s in to)

        used = await self._usage()
        new = sorted(new, key=lambda job: not any_pro(waiting(job, used)))
        checked, free_spent = 0, False
        for job in new:
            if checked >= PER_RUN:
                break
            to = waiting(job, used)
            if not to or (free_spent and not any_pro(to)):
                continue  # unchecked: it waits for tomorrow while it is fresh
            try:
                outcome = await self._process(http, job, to, monthly, now)
            except Exception:
                log.exception("Checking %s failed", job.url)
                outcome = Outcome.CHECKED
            if outcome is Outcome.STOP:
                break
            if outcome is Outcome.SKIPPED:
                free_spent = True  # the rest of the free-only jobs wait as well
                continue
            checked += 1
            used = await self._usage()  # cards and checks have changed

    async def _usage(self) -> dict[int, UserDay]:
        async with self.session_factory() as session:
            return await repo.usage(session, self.today())

    async def _read_mail(self, subs: list[Subscriber], now: datetime) -> list[sources.RawJob]:
        """Jobs from the job alert emails subscribers sent to their personal addresses."""
        letters, self.unread = self.unread, []
        try:
            raws = await asyncio.to_thread(fetch_unseen, self.mail)
        except (OSError, imaplib.IMAP4.error) as e:
            log.warning("Mailbox failed: %s", e)
            raws = []
        for raw in raws:
            try:
                letter = await asyncio.to_thread(read_letter, raw)
            except Exception:
                # The box already marked it read: one odd letter mustn't cost the others
                log.exception("A letter couldn't be read")
                continue
            if letter is not None:
                letters.append(letter)
        active = {s.id: s for s in subs}
        jobs: list[sources.RawJob] = []
        for letter in letters:
            try:
                jobs += await self._letter(letter, active, now)
            except Exception:
                log.exception("A letter from %s failed", letter.sender)
        return jobs

    async def _letter(
        self, letter: Letter, active: dict[int, Subscriber], now: datetime
    ) -> list[sources.RawJob]:
        async with self.session_factory() as session:
            owner = await repo.by_mail_token(session, letter.token)
        if owner is None:
            return []  # nobody has this address
        if confirmation := gmail_confirmation(letter):
            # Gmail asks to confirm forwarding before it sends anything on
            code, link = confirmation
            t = TEXTS[owner.lang]
            text = t.MAIL_CONFIRM.format(code=escape(code), link=escape(link))
            await safe_send(self.bot, owner.id, text)
            return []
        sub = active.get(owner.id)
        if sub is None:
            return []  # paused or searching for nothing
        found = await self._letter_jobs(sub, letter, now)
        if found is None and now - letter.received <= MAX_AGE and len(self.unread) < UNREAD_MAX:
            self.unread.append(letter)  # read it once the checks or the budget allow
        return found or []

    async def _letter_jobs(
        self, sub: Subscriber, letter: Letter, now: datetime
    ) -> list[sources.RawJob] | None:
        """The jobs in one letter; None if it can't be read today (no checks left)."""
        async with self.session_factory() as session:
            day = (await repo.usage(session, self.today())).get(sub.id)
        if (day.checks if day else 0) >= self.access.plan(sub, now).own_checks:
            log.info("Letter for %s waits: own checks used up today", sub.id)
            return None
        if not await self.take_check(self.access.is_pro(sub, now)):
            return None
        found, cost = await self.analyzer.read_letter(letter.subject, letter.text, letter.links)
        async with self.session_factory() as session:
            await repo.add_ai_cost(session, self.today(), cost)
            await repo.add_usage(session, sub.id, self.today(), checks=1)
        return [
            sources.RawJob(
                source=f"📬 {letter.sender}",
                # Per reader: two people forwarding the same alert both get its jobs
                external_id=hashlib.sha1(f"{sub.id}:{j.url}".encode()).hexdigest(),
                title=j.title,
                text=j.details,
                url=j.url,
                published=letter.received,
                feed=f"mail:{sub.id}",
            )
            for j in found or []
        ]

    async def _within_budget(self, monthly: float, any_pro: bool) -> bool | None:
        """True to check; False to skip this job; None when nothing more can be spent today.
        Free users only spend the base budget, so Pro subscribers' share stays theirs."""
        today_usd, _ = await self.spent()
        days = self.days_in_month()
        if today_usd >= monthly / days:
            log.warning("Today's AI budget of $%.3f is spent", monthly / days)
            return None
        return any_pro or today_usd < self.access.plans.base_usd / days

    async def _process(
        self,
        http: aiohttp.ClientSession,
        job: sources.RawJob,
        to: list[Subscriber],
        monthly: float,
        now: datetime,
    ) -> Outcome:
        """Check one job and send it to whoever it suits."""
        allowed = await self._within_budget(monthly, any(self.access.is_pro(s, now) for s in to))
        if allowed is None:
            return Outcome.STOP
        if not allowed:
            return Outcome.SKIPPED
        job = await sources.with_details(http, job)
        langs = sorted({s.lang for s in to})
        # Only the searches of the people this job may go to, so the AI sees a short list
        asked = sorted(
            searches_in(job, self.wanted.keywords)
            & {k for s in to for k in self.wanted.labels[s.id]}
        )
        first, done = await self._analyze(job, langs[0], to, asked, charge=True)
        if not done:
            return Outcome.STOP
        if first is None:
            await self._failed(job)
        else:
            self.failures.pop((job.source, job.external_id), None)
            await self._deliver(job, langs[0], first, to, asked, now)
        return Outcome.CHECKED

    async def _deliver(
        self,
        job: sources.RawJob,
        lang: str,
        first: Analysis,
        to: list[Subscriber],
        asked: list[str],
        now: datetime,
    ) -> None:
        """Remember the checked job and send it to those it suits, each in their language."""
        keys = self.wanted.keys_of()
        fits = [s for s in to if mismatch(s, keys[s.id], first) is None]
        rejected_for = None if fits else mismatch(to[0], keys[to[0].id], first)
        async with self.session_factory() as session:
            recorded = await repo.record(session, job, first, rejected_for)
        if not recorded:
            return  # a parallel run got it first
        if rejected_for:
            log.info("Rejected %s: %s (asked %s)", job.url, rejected_for, asked)
            return
        # The facts are the same in every language; only the texts need translating
        analyses = {lang: first}
        for other in sorted({s.lang for s in fits} - {lang}):
            analysis, done = await self._analyze(job, other, fits, asked, charge=False)
            if analysis is not None:
                analyses[other] = analysis
            if not done:
                break
        for sub in fits:
            await self._send(sub, job, analyses.get(sub.lang, first), now)

    async def _failed(self, job: sources.RawJob) -> None:
        """No usable answer: the job is tried again next run, but one the AI keeps failing
        on (a refusal, an answer too long) is put aside instead of being paid for forever."""
        key = (job.source, job.external_id)
        self.failures[key] = self.failures.get(key, 0) + 1
        if self.failures[key] >= AI_TRIES:
            del self.failures[key]
            async with self.session_factory() as session:
                await repo.record(session, job, None, "ai")

    async def _analyze(
        self, job: sources.RawJob, lang: str, to: list[Subscriber], asked: list[str], charge: bool
    ) -> tuple[Analysis | None, bool]:
        """The facts in one language, and False once the daily check limit is reached.
        `charge`: count it against the recipients' own checks, once per job."""
        async with self.session_factory() as session:
            if not await repo.reserve_ai_check(session, self.today(), self.ai_daily_limit):
                log.warning("Daily AI limit reached, the rest waits for tomorrow")
                return None, False
        analysis, cost = await self.analyzer.analyze(job, lang, asked)
        async with self.session_factory() as session:
            await repo.add_ai_cost(session, self.today(), cost)
            # Own sources spend their owners' checks
            if charge and job.feed not in self.global_keys:
                for sub in to:
                    await repo.add_usage(session, sub.id, self.today(), checks=1)
        return analysis, True

    async def _send(self, sub: Subscriber, job: sources.RawJob, a: Analysis, now: datetime) -> None:
        if sub.only_top and not a.top:
            return
        t = TEXTS[sub.lang]
        sent = await safe_send(
            self.bot,
            sub.id,
            card(job, a, t, self.wanted.labels_for(sub.id, a.matches)),
            reply_markup=open_job(t, job.url),
            disable_web_page_preview=True,
        )
        if not sent:
            return
        async with self.session_factory() as session:
            await repo.add_usage(session, sub.id, self.today(), cards=1)
            day = (await repo.usage(session, self.today()))[sub.id]
        plan = self.access.plan(sub, now)
        if day.cards == plan.cards:
            text = t.LIMIT_REACHED.format(cards=plan.cards)
            if not self.access.is_pro(sub, now):
                text += t.LIMIT_UPSELL.format(cards=self.access.plans.pro.cards)
            await safe_send(self.bot, sub.id, text)

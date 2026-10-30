"""All database queries of the bot live here."""

from datetime import date, datetime

from sqlalchemy import delete, func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from jobradar.ai import Analysis
from jobradar.mail import new_token
from jobradar.models import (
    SOURCE_MAX,
    AiUsage,
    Job,
    JobStatus,
    Subscriber,
    UserDay,
    UserSearch,
    UserSource,
)
from jobradar.sources import RawJob

# --- Subscribers ---


async def get_subscriber(session: AsyncSession, user_id: int) -> Subscriber | None:
    return await session.get(Subscriber, user_id)


async def subscribe(session: AsyncSession, user_id: int, lang: str) -> Subscriber:
    sub = await session.get(Subscriber, user_id)
    if sub is None:
        # A starting guess from the interface language; /filters changes it
        slavic = lang in ("uk", "ru")
        sub = Subscriber(
            id=user_id,
            lang=lang,
            active=True,
            only_top=False,
            languages=["en", "uk", "ru"] if slavic else list(dict.fromkeys(["en", lang])),
            country="UA" if slavic else {"pl": "PL"}.get(lang, "XX"),
        )
        session.add(sub)
    sub.active = True
    await session.commit()
    return sub


async def active_subscribers(session: AsyncSession) -> list[Subscriber]:
    return list(await session.scalars(select(Subscriber).where(Subscriber.active)))


async def activate_pro(
    session: AsyncSession, sub: Subscriber, until: datetime, charge_id: str
) -> None:
    sub.pro_until, sub.pro_charge_id = until, charge_id
    await session.commit()


async def revoke_pro(session: AsyncSession, user_id: int, charge_id: str) -> bool:
    """A refunded payment takes back the Pro it paid for; False if that wasn't the
    payment the current Pro stands on."""
    sub = await session.get(Subscriber, user_id)
    if sub is None or sub.pro_charge_id != charge_id:
        return False
    sub.pro_until, sub.pro_charge_id = None, None
    await session.commit()
    return True


async def paying_count(session: AsyncSession, now: datetime) -> int:
    """Subscribers with a paid Pro right now: each one adds to the AI budget. A gift
    brings no money, so it doesn't."""
    return (
        await session.scalar(
            select(func.count()).select_from(Subscriber).where(Subscriber.pro_until > now)
        )
        or 0
    )


async def set_gift(session: AsyncSession, user_id: int, on: bool) -> Subscriber | None:
    """Give or take back a permanent free Pro; None if the user never started the bot."""
    sub = await session.get(Subscriber, user_id)
    if sub is None:
        return None
    sub.gift = on
    await session.commit()
    return sub


async def mail_token(session: AsyncSession, sub: Subscriber) -> str:
    """The subscriber's personal mail address suffix, made the first time it is asked for."""
    if sub.mail_token is None:
        sub.mail_token = new_token()
        await session.commit()
    return sub.mail_token


async def by_mail_token(session: AsyncSession, token: str) -> Subscriber | None:
    return await session.scalar(select(Subscriber).where(Subscriber.mail_token == token))


async def _lock(session: AsyncSession, user_id: int) -> None:
    """Hold the subscriber's row until commit: two quick adds then take turns, so both
    can't fit under the same limit."""
    await session.execute(select(Subscriber.id).where(Subscriber.id == user_id).with_for_update())


# --- Searches ---


async def user_searches(session: AsyncSession, user_id: int) -> list[UserSearch]:
    return list(
        await session.scalars(
            select(UserSearch).where(UserSearch.user_id == user_id).order_by(UserSearch.id)
        )
    )


async def add_search(
    session: AsyncSession, user_id: int, label: str, keywords: list[str], limit: int
) -> bool | None:
    """True if added, False if this subscriber already has it, None if their plan's
    limit is reached."""
    await _lock(session, user_id)
    count = await session.scalar(
        select(func.count()).select_from(UserSearch).where(UserSearch.user_id == user_id)
    )
    if count >= limit:
        await session.commit()
        return None
    result = await session.execute(
        pg_insert(UserSearch)
        .values(user_id=user_id, label=label, keywords=keywords)
        .on_conflict_do_nothing()
        .returning(UserSearch.id)
    )
    await session.commit()
    return result.scalar() is not None


async def remove_search(session: AsyncSession, user_id: int, search_id: int) -> None:
    await session.execute(
        delete(UserSearch).where(UserSearch.id == search_id, UserSearch.user_id == user_id)
    )
    await session.commit()


async def searches_of(session: AsyncSession, user_ids: list[int]) -> list[UserSearch]:
    """Everyone's searches, oldest first."""
    return list(
        await session.scalars(
            select(UserSearch).where(UserSearch.user_id.in_(user_ids)).order_by(UserSearch.id)
        )
    )


# --- Own sources ---


async def user_sources(session: AsyncSession, user_id: int) -> list[UserSource]:
    return list(
        await session.scalars(
            select(UserSource).where(UserSource.user_id == user_id).order_by(UserSource.id)
        )
    )


async def add_source(
    session: AsyncSession, user_id: int, kind: str, ref: str, limit: int
) -> bool | None:
    """True if added, False if this subscriber already has it, None if their plan's
    limit is reached."""
    await _lock(session, user_id)
    count = await session.scalar(
        select(func.count()).select_from(UserSource).where(UserSource.user_id == user_id)
    )
    if count >= limit:
        await session.commit()
        return None
    result = await session.execute(
        pg_insert(UserSource)
        .values(user_id=user_id, kind=kind, ref=ref)
        .on_conflict_do_nothing()
        .returning(UserSource.id)
    )
    await session.commit()
    return result.scalar() is not None


async def remove_source(session: AsyncSession, user_id: int, source_id: int) -> None:
    await session.execute(
        delete(UserSource).where(UserSource.id == source_id, UserSource.user_id == user_id)
    )
    await session.commit()


async def sources_of(session: AsyncSession, user_ids: list[int]) -> dict[int, list[str]]:
    """Feed keys of each subscriber's own sources, oldest first."""
    rows = await session.scalars(
        select(UserSource).where(UserSource.user_id.in_(user_ids)).order_by(UserSource.id)
    )
    keys: dict[int, list[str]] = {}
    for source in rows:
        keys.setdefault(source.user_id, []).append(source.key)
    return keys


# --- Per-user daily usage ---


async def usage(session: AsyncSession, today: date) -> dict[int, UserDay]:
    rows = await session.scalars(select(UserDay).where(UserDay.day == today))
    return {row.user_id: row for row in rows}


async def add_usage(
    session: AsyncSession, user_id: int, today: date, cards: int = 0, checks: int = 0
) -> None:
    await session.execute(
        pg_insert(UserDay)
        .values(user_id=user_id, day=today, cards=cards, checks=checks)
        .on_conflict_do_update(
            index_elements=[UserDay.user_id, UserDay.day],
            set_={"cards": UserDay.cards + cards, "checks": UserDay.checks + checks},
        )
    )
    await session.commit()


# --- Jobs ---


async def unseen(session: AsyncSession, jobs: list[RawJob]) -> list[RawJob]:
    """Jobs the AI hasn't looked at yet."""
    if not jobs:
        return []
    ids = {j.external_id for j in jobs}
    rows = await session.execute(
        select(Job.source, Job.external_id).where(Job.external_id.in_(ids))
    )
    seen = set(rows.tuples())
    return [j for j in jobs if (j.source[:SOURCE_MAX], j.external_id) not in seen]


async def record(
    session: AsyncSession, job: RawJob, analysis: Analysis | None, rejected_for: str | None
) -> bool:
    """Remember a checked job, with the filter it failed for everyone (None = someone got
    it). No analysis: the AI couldn't read it. False if it was already recorded (e.g. by
    a parallel run)."""
    result = await session.execute(
        pg_insert(Job)
        .values(
            source=job.source[:SOURCE_MAX],
            external_id=job.external_id,
            title=job.title[:512],
            url=job.url[:1024],
            status=JobStatus.REJECTED if rejected_for else JobStatus.SENT,
            niche=analysis.niche if analysis else "",
            reason=rejected_for or "",
        )
        .on_conflict_do_nothing()
        .returning(Job.id)
    )
    await session.commit()
    return result.scalar() is not None


# --- Daily AI budget ---


async def reserve_ai_check(session: AsyncSession, today: date, limit: int) -> bool:
    """Atomically take one AI check from today's budget; False when it is used up."""
    if limit <= 0:
        return False  # the insert below would let the day's first check through
    result = await session.execute(
        pg_insert(AiUsage)
        .values(day=today, checks=1)
        .on_conflict_do_update(
            index_elements=[AiUsage.day],
            set_={"checks": AiUsage.checks + 1},
            where=AiUsage.checks < limit,
        )
        .returning(AiUsage.checks)
    )
    await session.commit()
    return result.scalar() is not None


async def ai_checks(session: AsyncSession, today: date) -> int:
    usage = await session.get(AiUsage, today)
    return usage.checks if usage else 0


async def add_ai_cost(session: AsyncSession, today: date, usd: float) -> None:
    micro = round(usd * 1_000_000)
    await session.execute(
        pg_insert(AiUsage)
        .values(day=today, checks=0, cost_micro=micro)
        .on_conflict_do_update(
            index_elements=[AiUsage.day], set_={"cost_micro": AiUsage.cost_micro + micro}
        )
    )
    await session.commit()


async def ai_spent(session: AsyncSession, since: date, until: date) -> float:
    """USD spent on days since..until, both included."""
    micro = await session.scalar(
        select(func.coalesce(func.sum(AiUsage.cost_micro), 0)).where(
            AiUsage.day >= since, AiUsage.day <= until
        )
    )
    return micro / 1_000_000

"""Who gets a job and how much of the AI budget may be spent on it."""

from dataclasses import dataclass
from datetime import datetime

from jobradar.config import Plan, Plans
from jobradar.models import Subscriber, UserDay, UserSearch


@dataclass(frozen=True)
class Access:
    plans: Plans
    admin_ids: set[int]

    def is_pro(self, sub: Subscriber, now: datetime) -> bool:
        return (
            sub.id in self.admin_ids
            or sub.gift
            or (sub.pro_until is not None and sub.pro_until > now)
        )

    def plan(self, sub: Subscriber, now: datetime) -> Plan:
        return self.plans.pro if self.is_pro(sub, now) else self.plans.free

    def monthly_usd(self, paying: int) -> float:
        return self.plans.base_usd + self.plans.usd_per_pro * paying


def recipients(
    feed: str,
    matched: set[str],
    subs: list[Subscriber],
    searches: dict[int, set[str]],
    global_keys: set[str],
    own: dict[int, set[str]],
    used: dict[int, UserDay],
    access: Access,
    now: datetime,
) -> list[Subscriber]:
    """Subscribers who may get a job from this feed, whose words point to their
    `matched` searches, today. Nobody -> the job isn't checked at all, so it costs nothing and
    waits for tomorrow while it is fresh."""
    shared = feed in global_keys
    result = []
    for sub in subs:
        if not matched & searches.get(sub.id, set()):
            continue
        if not shared and feed not in own.get(sub.id, set()):
            continue
        plan, day = access.plan(sub, now), used.get(sub.id)
        cards, checks = (day.cards, day.checks) if day else (0, 0)
        if cards >= plan.cards:
            continue
        # A user's own sources spend their own checks, so one noisy channel can't eat
        # everyone's budget
        if not shared and checks >= plan.own_checks:
            continue
        result.append(sub)
    return result


def within_plans(
    subs: list[Subscriber],
    sources: dict[int, list[str]],
    searches: list[UserSearch],
    access: Access,
    now: datetime,
) -> tuple[dict[int, set[str]], list[UserSearch]]:
    """The own sources and searches each subscriber's plan lets work, oldest first: after
    Pro ends, what was added beyond the Free limits rests until Pro is back."""
    plans = {sub.id: access.plan(sub, now) for sub in subs}
    own = {
        user_id: set(keys[: plans[user_id].sources])
        for user_id, keys in sources.items()
        if user_id in plans
    }
    taken: dict[int, int] = {}
    kept = []
    for search in searches:
        if search.user_id not in plans:
            continue
        taken[search.user_id] = taken.get(search.user_id, 0) + 1
        if taken[search.user_id] <= plans[search.user_id].searches:
            kept.append(search)
    return own, kept

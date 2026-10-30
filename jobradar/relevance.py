"""Cheap checks before the AI: is it fresh, and does it mention any of the searches."""

import re
from collections.abc import Mapping
from datetime import datetime, timedelta

from jobradar.searches import matching
from jobradar.sources import RawJob

# Older posts are not "hot" any more
MAX_AGE = timedelta(days=2)
# People offering their own services, not employers. A bare "резюме" stays out: employers
# write it too ("резюме в лс")
OFFERS = re.compile(r"\[\s*for\s*hire\s*\]|#резюме|шукаю роботу|ищу работу", re.I)


def is_fresh(job: RawJob, now: datetime) -> bool:
    return now - job.published <= MAX_AGE


def searches_in(job: RawJob, searches: Mapping[str, list[str]]) -> set[str]:
    """Which searches the post's words point to; empty for self-ads."""
    if OFFERS.search(job.title):
        return set()
    return matching(job.title, job.text, searches)


def candidates(
    jobs: list[RawJob], now: datetime, searches: Mapping[str, list[str]]
) -> list[RawJob]:
    """Fresh jobs about any of the searches, oldest first, each one once."""
    seen: set[tuple[str, str]] = set()
    result = []
    for job in sorted(jobs, key=lambda j: j.published):
        key = (job.source, job.external_id)
        if key not in seen and is_fresh(job, now) and searches_in(job, searches):
            seen.add(key)
            result.append(job)
    return result

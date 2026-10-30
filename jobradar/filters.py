"""A subscriber's filters against the facts the AI read from a post."""

from jobradar.ai import Analysis, Pay, Region, Remote, Schedule
from jobradar.models import Subscriber

# EU and EEA: "EU residents only" jobs are open to all of them
EU_COUNTRIES = frozenset(
    {
        *("AT", "BE", "BG", "HR", "CY", "CZ", "DK", "EE", "FI", "FR", "DE", "GR", "HU", "IE"),
        *("IT", "LV", "LT", "LU", "MT", "NL", "PL", "PT", "RO", "SK", "SI", "ES", "SE"),
        *("IS", "LI", "NO"),
    }
)
# Countries offered in the filters; "XX" stands for any other
COUNTRIES = ("UA", "PL", "DE", "CZ", "ES", "GB", "US", "XX")
LANGUAGES = ("en", "uk", "ru", "pl", "de", "es")


def lives_in(country: str, residency: frozenset[str]) -> bool:
    return country in residency or ("EU" in residency and country in EU_COUNTRIES)


def mismatch(sub: Subscriber, searches: set[str], a: Analysis) -> str | None:
    """The first filter the job fails, or None if it suits this subscriber. Anything the
    post doesn't say ("unknown", []) passes: it is better to show a job than lose it."""
    checks = (
        ("not_offer", not a.is_offer or a.scam),
        ("unpaid", a.paid in (Pay.UNPAID, Pay.REVENUE_SHARE)),
        ("search", not a.matches & searches),
        ("onsite", a.remote == Remote.ONSITE or (sub.remote_only and a.remote == Remote.HYBRID)),
        ("schedule", sub.flexible_only and a.schedule == Schedule.FIXED),
        ("languages", bool(a.languages - set(sub.languages))),
        ("region", a.employer_region in Region.CHOOSABLE and a.employer_region not in sub.regions),
        ("residency", bool(a.residency) and not lives_in(sub.country, a.residency)),
    )
    return next((name for name, failed in checks if failed), None)

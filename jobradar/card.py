"""A job as a Telegram message."""

from html import escape

from jobradar.ai import Analysis, Niche
from jobradar.sources import RawJob
from jobradar.texts import Ru


def card(job: RawJob, a: Analysis, t: Ru, labels: list[str]) -> str:
    """`labels` are the reader's own searches this job matched."""
    video = a.niche != Niche.OTHER
    icon = "🔥" if a.top else "🎬" if video else "💼"
    software = ", ".join(a.software) or t.NOT_STATED
    kind = escape(" / ".join(labels))
    if video:
        kind += f" · {t.NICHES[a.niche]}"
    lines = [
        f"{icon} <b>{escape(a.title or job.title)}</b>",
        f"<i>{kind}</i>",
        "",
        f"📝 <b>{t.CARD_DUTIES}:</b> {escape(a.duties or t.NOT_STATED)}",
        f"🛠 <b>{t.CARD_SOFTWARE}:</b> {escape(software)}",
        f"🌍 <b>{t.CARD_COUNTRY}:</b> {escape(a.country or t.NOT_STATED)}",
        f"💰 <b>{t.CARD_PAY}:</b> {escape(a.pay or t.NOT_STATED)}",
    ]
    if a.summary:
        label = t.CARD_TRANSLATION if a.translated else t.CARD_SUMMARY
        lines += ["", f"🔤 <b>{label}:</b> {escape(a.summary)}"]
    lines += ["", f"📍 {t.CARD_SOURCE}: {escape(job.source)}"]
    return "\n".join(lines)

"""Database tables: subscribers, jobs already looked at, the daily AI budget."""

from datetime import date, datetime

from sqlalchemy import BigInteger, DateTime, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Subscriber(Base):
    __tablename__ = "subscribers"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=False)
    lang: Mapped[str] = mapped_column(String(8))
    active: Mapped[bool] = mapped_column(default=True)
    # Only podcasts and talking heads, or every suitable job
    only_top: Mapped[bool] = mapped_column(default=False)
    # Filters (what work to look for is in UserSearch)
    remote_only: Mapped[bool] = mapped_column(default=True)  # no hybrid
    flexible_only: Mapped[bool] = mapped_column(default=True)  # no fixed hours
    languages: Mapped[list[str]] = mapped_column(
        ARRAY(String(8)), default=lambda: ["en", "uk", "ru"]
    )
    regions: Mapped[list[str]] = mapped_column(
        ARRAY(String(16)), default=lambda: ["us", "eu", "ua"]
    )
    country: Mapped[str] = mapped_column(String(8), default="UA")
    pro_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
    # The last Stars payment, needed to refund it
    pro_charge_id: Mapped[str | None] = mapped_column(String(256), default=None)
    # Pro given by the owner for free and for good; a paid subscription is kept apart
    gift: Mapped[bool] = mapped_column(default=False)
    # The +suffix of the personal address for job alert emails; made on first use
    mail_token: Mapped[str | None] = mapped_column(String(16), unique=True, default=None)


class UserSearch(Base):
    """What work a subscriber looks for, in their own words, e.g. "моушн-дизайнер".
    The keywords (several languages, made by the AI once) find matching posts."""

    __tablename__ = "user_searches"
    __table_args__ = (UniqueConstraint("user_id", "label"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, index=True)
    label: Mapped[str] = mapped_column(String(64))
    keywords: Mapped[list[str]] = mapped_column(ARRAY(String(64)))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class SourceKind:
    TELEGRAM = "tg"  # public channel name
    REDDIT = "reddit"  # subreddit name
    RSS = "rss"  # feed URL

    ALL = (TELEGRAM, REDDIT, RSS)


class UserSource(Base):
    """A source a subscriber added by link: its jobs go only to the people who added it."""

    __tablename__ = "user_sources"
    __table_args__ = (UniqueConstraint("user_id", "kind", "ref"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, index=True)
    kind: Mapped[str] = mapped_column(String(16))
    ref: Mapped[str] = mapped_column(String(512))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    @property
    def key(self) -> str:
        """Matches RawJob.feed of the jobs this source produces."""
        return f"{self.kind}:{self.ref}"


class UserDay(Base):
    """What one subscriber used on one day: cards received and AI checks of own sources."""

    __tablename__ = "user_days"

    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=False)
    day: Mapped[date] = mapped_column(primary_key=True)
    cards: Mapped[int] = mapped_column(default=0)
    checks: Mapped[int] = mapped_column(default=0)


SOURCE_MAX = 128  # characters of Job.source; longer names are cut to fit


class JobStatus:
    SENT = "sent"  # suitable, sent to subscribers
    REJECTED = "rejected"  # the AI said it doesn't fit


class Job(Base):
    """A job the AI has looked at, so it is never checked or sent twice."""

    __tablename__ = "jobs"
    __table_args__ = (UniqueConstraint("source", "external_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    source: Mapped[str] = mapped_column(String(SOURCE_MAX))
    external_id: Mapped[str] = mapped_column(String(128))
    title: Mapped[str] = mapped_column(String(512))
    url: Mapped[str] = mapped_column(String(1024))
    status: Mapped[str] = mapped_column(String(16))
    niche: Mapped[str] = mapped_column(String(32), default="")
    reason: Mapped[str] = mapped_column(String(512), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AiUsage(Base):
    __tablename__ = "ai_usage"

    day: Mapped[date] = mapped_column(primary_key=True)
    checks: Mapped[int] = mapped_column(default=0)
    # Spent that day, in millionths of a dollar so the sum stays exact
    cost_micro: Mapped[int] = mapped_column(BigInteger, default=0)

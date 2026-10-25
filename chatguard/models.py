from datetime import date, datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, String, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Action:
    DELETE = "delete"  # only remove the message
    MUTE = "mute"  # remove and forbid writing
    BAN = "ban"  # remove and kick out of the group

    ALL = (DELETE, MUTE, BAN)


class Chat(Base):
    __tablename__ = "chats"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=False)
    title: Mapped[str] = mapped_column(String(256))
    lang: Mapped[str] = mapped_column(String(8))
    enabled: Mapped[bool] = mapped_column(default=True)
    action: Mapped[str] = mapped_column(String(16), default=Action.MUTE)
    checked: Mapped[int] = mapped_column(default=0)
    caught: Mapped[int] = mapped_column(default=0)
    # Daily AI budget per chat
    ai_day: Mapped[date | None]
    ai_checks: Mapped[int] = mapped_column(default=0)
    # Pro subscription (Telegram Stars), paid by one of the admins
    pro_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    pro_owner_id: Mapped[int | None] = mapped_column(BigInteger)
    pro_charge_id: Mapped[str | None] = mapped_column(String(512))


class Spammer(Base):
    """Shared across chats: people caught spamming anywhere. Pro chats check them harder."""

    __tablename__ = "spammers"

    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=False)
    caught: Mapped[int] = mapped_column(default=0)
    last_caught_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class Member(Base):
    """What the bot knows about a person in a chat. Only newcomers' first messages are checked."""

    __tablename__ = "members"

    chat_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("chats.id"), primary_key=True, autoincrement=False
    )
    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=False)
    clean_messages: Mapped[int] = mapped_column(default=0)
    # Set when an admin restores someone the bot caught by mistake
    trusted: Mapped[bool] = mapped_column(default=False)


class Incident(Base):
    """A message the bot removed, kept so an admin can undo the decision."""

    __tablename__ = "incidents"

    id: Mapped[int] = mapped_column(primary_key=True)
    chat_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("chats.id"), index=True)
    user_id: Mapped[int] = mapped_column(BigInteger)
    user_name: Mapped[str] = mapped_column(String(128))
    text: Mapped[str] = mapped_column(String(4096))
    source: Mapped[str] = mapped_column(String(16))  # rules | haiku | opus
    reason: Mapped[str] = mapped_column(String(512))
    action: Mapped[str] = mapped_column(String(16))
    restored: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

"""Money is stored as integers in minor units (kopecks/cents) to avoid float rounding."""

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, String, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

# A Telegram full name can be one longer (64-character first and last names and a space)
NAME_LENGTH = 128


class Base(DeclarativeBase):
    pass


class Chat(Base):
    __tablename__ = "chats"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=False)
    title: Mapped[str] = mapped_column(String(256))
    currency: Mapped[str] = mapped_column(String(8), default="₴")
    lang: Mapped[str] = mapped_column(String(8), default="ru", server_default="ru")


class Member(Base):
    """A person taking part in the chat's expenses (joined via the button or by paying).
    Someone who left keeps the row: their name still shows in balances and history."""

    __tablename__ = "members"

    chat_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("chats.id"), primary_key=True, autoincrement=False
    )
    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=False)
    name: Mapped[str] = mapped_column(String(NAME_LENGTH))
    username: Mapped[str | None] = mapped_column(String(64))
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    # False after /leave or leaving the group: new expenses aren't split with them
    active: Mapped[bool] = mapped_column(default=True, server_default="true")


class Expense(Base):
    __tablename__ = "expenses"

    id: Mapped[int] = mapped_column(primary_key=True)
    chat_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("chats.id"), index=True)
    payer_id: Mapped[int] = mapped_column(BigInteger)
    amount: Mapped[int] = mapped_column(BigInteger)
    description: Mapped[str] = mapped_column(String(128))
    is_deleted: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    shares: Mapped[list["Share"]] = relationship(
        lazy="selectin", cascade="all, delete-orphan", order_by="Share.user_id"
    )


class Share(Base):
    """How much of an expense falls on one person."""

    __tablename__ = "shares"

    expense_id: Mapped[int] = mapped_column(ForeignKey("expenses.id"), primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=False)
    amount: Mapped[int] = mapped_column(BigInteger)
    # Set by hand ("who pays how much"); the others split the rest equally
    fixed: Mapped[bool] = mapped_column(default=False, server_default="false")


class Settlement(Base):
    """A debt paid back outside the bot: `from_id` gave `amount` to `to_id`."""

    __tablename__ = "settlements"

    id: Mapped[int] = mapped_column(primary_key=True)
    chat_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("chats.id"), index=True)
    from_id: Mapped[int] = mapped_column(BigInteger)
    to_id: Mapped[int] = mapped_column(BigInteger)
    amount: Mapped[int] = mapped_column(BigInteger)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

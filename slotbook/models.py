from datetime import datetime, time

from sqlalchemy import BigInteger, DateTime, ForeignKey, String, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Service(Base):
    __tablename__ = "services"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(64))
    duration_min: Mapped[int]
    price: Mapped[int]
    # Services are hidden instead of deleted so old bookings keep their service
    is_active: Mapped[bool] = mapped_column(default=True)


class WorkDay(Base):
    """Working hours for a weekday. start/end = None means a day off."""

    __tablename__ = "work_days"

    weekday: Mapped[int] = mapped_column(primary_key=True)  # 0 = Monday
    start: Mapped[time | None]
    end: Mapped[time | None]


class BookingStatus:
    ACTIVE = "active"
    CANCELLED = "cancelled"


class Booking(Base):
    __tablename__ = "bookings"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, index=True)
    user_name: Mapped[str] = mapped_column(String(128))
    username: Mapped[str | None] = mapped_column(String(64))
    service_id: Mapped[int] = mapped_column(ForeignKey("services.id"))
    service: Mapped[Service] = relationship(lazy="joined")
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(16), default=BookingStatus.ACTIVE)
    reminded_24h: Mapped[bool] = mapped_column(default=False)
    reminded_2h: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

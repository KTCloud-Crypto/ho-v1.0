import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Boolean, DateTime, ForeignKey, UniqueConstraint, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db import Base


def _now():
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    telegram_chat_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    webhook_token: Mapped[str] = mapped_column(
        String(36), unique=True, index=True, default=lambda: str(uuid.uuid4())
    )
    bot_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    exchange_key: Mapped["ExchangeKey"] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    positions: Mapped[list["Position"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    trades: Mapped[list["Trade"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class ExchangeKey(Base):
    __tablename__ = "exchange_keys"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)
    encrypted_access_key: Mapped[str] = mapped_column(String(512))
    encrypted_secret_key: Mapped[str] = mapped_column(String(512))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    user: Mapped["User"] = relationship(back_populates="exchange_key")


class Position(Base):
    __tablename__ = "positions"
    __table_args__ = (UniqueConstraint("user_id", "ticker", name="uq_position_user_ticker"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    ticker: Mapped[str] = mapped_column(String(32))
    status: Mapped[str | None] = mapped_column(String(16), nullable=True)  # "long" or None
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now)

    user: Mapped["User"] = relationship(back_populates="positions")


class Trade(Base):
    __tablename__ = "trades"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    ticker: Mapped[str] = mapped_column(String(32))
    action: Mapped[str] = mapped_column(String(8))  # buy/sell
    price: Mapped[float | None] = mapped_column(nullable=True)
    volume: Mapped[float | None] = mapped_column(nullable=True)
    status: Mapped[str] = mapped_column(String(16))  # success/failed
    raw_response: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    user: Mapped["User"] = relationship(back_populates="trades")

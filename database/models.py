"""
مدل‌های SQLAlchemy پروژه.
جدول‌ها: users, configs, broadcast_logs, banned_users
"""
from __future__ import annotations

import datetime as dt
import enum
from typing import List, Optional

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


def utcnow() -> dt.datetime:
    return dt.datetime.utcnow()


class ConfigStatus(str, enum.Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    DISABLED = "disabled"
    DELETED = "deleted"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True, nullable=False)
    username: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    first_name: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    is_banned: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=utcnow, nullable=False)
    last_seen_at: Mapped[dt.datetime] = mapped_column(DateTime, default=utcnow, nullable=False)

    configs: Mapped[List["Config"]] = relationship(
        "Config", back_populates="user", cascade="all, delete-orphan"
    )


class Config(Base):
    __tablename__ = "configs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.telegram_id"), index=True, nullable=False)

    name: Mapped[str] = mapped_column(String(128), nullable=False)
    # uuid همان uid واقعی ردیف links در پنل SulgX است (پنل مفهوم Inbound
    # جداگانه‌ای ندارد؛ یک سرور/دامنه‌ی واحد است).
    uuid: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)

    volume_gb: Mapped[float] = mapped_column(Float, nullable=False)
    used_volume_gb: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    max_connections: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    validity_days: Mapped[int] = mapped_column(Integer, nullable=False)

    link: Mapped[str] = mapped_column(Text, nullable=False)
    subscription_link: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    status: Mapped[ConfigStatus] = mapped_column(
        Enum(ConfigStatus), default=ConfigStatus.ACTIVE, nullable=False
    )

    expire_date: Mapped[dt.datetime] = mapped_column(DateTime, nullable=False)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=utcnow, nullable=False)
    last_connection_at: Mapped[Optional[dt.datetime]] = mapped_column(DateTime, nullable=True)

    user: Mapped["User"] = relationship("User", back_populates="configs")


class RequiredChannel(Base):
    """کانال‌های عضویت اجباری - قابل مدیریت از پنل ادمین بدون نیاز به ریستارت کد."""

    __tablename__ = "required_channels"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    chat_id: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    title: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    invite_url: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=utcnow, nullable=False)


class BroadcastLog(Base):
    __tablename__ = "broadcast_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    admin_telegram_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    message_text: Mapped[str] = mapped_column(Text, nullable=False)
    total_targets: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    success_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    failed_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=utcnow, nullable=False)

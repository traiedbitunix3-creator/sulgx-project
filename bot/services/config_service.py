"""
این فایل قبلاً یک کپی کامل از backend/services/config_service.py بود (منطق
ساخت/تمدید/حذف کانفیگ در دو جای مجزا تکرار شده بود - یکی از باگ‌های
duplicate-logic که در بررسی پروژه پیدا شد). چون بات و بک‌اند هر دو روی
همان VPS و از همان دیتابیس SQLite استفاده می‌کنند، ربات به‌جای پیاده‌سازی
دوباره‌ی منطق، مستقیماً از سرویس بک‌اند (تنها منبع حقیقت) استفاده می‌کند.
"""
from __future__ import annotations

from typing import Optional

from backend.schemas import ConfigOut
from backend.services import config_service as backend_config_service
from database.session import get_session_ctx

SulgXUnavailableError = backend_config_service.SulgXUnavailableError
ConfigNotFoundError = backend_config_service.ConfigNotFoundError


async def create_config(
    telegram_id: int, name: str, volume_gb: float, validity_days: int, max_connections: int
) -> ConfigOut:
    async with get_session_ctx() as session:
        return await backend_config_service.create_config_for_user(
            session,
            telegram_id=telegram_id,
            name=name,
            volume_gb=volume_gb,
            validity_days=validity_days,
            max_connections=max_connections,
        )


async def get_latest_config(telegram_id: int) -> Optional[ConfigOut]:
    async with get_session_ctx() as session:
        configs = await backend_config_service.list_user_configs(session, telegram_id)
        return configs[0] if configs else None


async def list_configs(telegram_id: int) -> list[ConfigOut]:
    async with get_session_ctx() as session:
        return await backend_config_service.list_user_configs(session, telegram_id)


async def renew_config(telegram_id: int, config_uuid: str, *, add_volume_gb: float | None = None, extend_days: int | None = None) -> ConfigOut:
    async with get_session_ctx() as session:
        return await backend_config_service.renew_config(
            session, telegram_id=telegram_id, config_uuid=config_uuid, add_volume_gb=add_volume_gb, extend_days=extend_days
        )


async def reset_config_link(telegram_id: int, config_uuid: str) -> str:
    async with get_session_ctx() as session:
        return await backend_config_service.reset_config_link(session, telegram_id=telegram_id, config_uuid=config_uuid)


async def delete_config(telegram_id: int, config_uuid: str) -> None:
    async with get_session_ctx() as session:
        await backend_config_service.delete_config(session, telegram_id=telegram_id, config_uuid=config_uuid)


async def sync_usage_from_panel(telegram_id: int, config_uuid: str) -> ConfigOut:
    """حجم مصرف، حجم کل، expiry و active را از پنل واقعی SulgX می‌خواند و به‌روز می‌کند."""
    async with get_session_ctx() as session:
        return await backend_config_service.sync_usage_from_panel(
            session, telegram_id=telegram_id, config_uuid=config_uuid
        )

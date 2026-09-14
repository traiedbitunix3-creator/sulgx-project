import asyncio
import datetime as dt
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Config, ConfigStatus
from backend.schemas import ConfigOut
from sulgx_api import SulgXAPIError, SulgXLink, sulgx_client


class SulgXUnavailableError(Exception):
    pass


class ConfigNotFoundError(Exception):
    pass


def _to_out(config: Config) -> ConfigOut:
    remaining = max(config.volume_gb - config.used_volume_gb, 0)
    return ConfigOut(
        uuid=config.uuid,
        name=config.name,
        status=config.status.value,
        volume_gb=config.volume_gb,
        used_volume_gb=config.used_volume_gb,
        remaining_volume_gb=remaining,
        max_connections=config.max_connections,
        expire_date=config.expire_date,
        link=config.link,
        subscription_link=config.subscription_link,
        last_connection_at=config.last_connection_at,
    )


def _parse_expires_at(raw: Optional[str]) -> Optional[dt.datetime]:
    if not raw:
        return None
    try:
        value = raw.replace("Z", "+00:00") if raw.endswith("Z") else raw
        parsed = dt.datetime.fromisoformat(value)
        return parsed.replace(tzinfo=None) if parsed.tzinfo else parsed
    except ValueError:
        return None


async def list_user_configs(session: AsyncSession, telegram_id: int) -> List[ConfigOut]:
    result = await session.execute(
        select(Config).where(Config.telegram_id == telegram_id).order_by(Config.created_at.desc())
    )
    configs = result.scalars().all()
    return [_to_out(c) for c in configs]


async def create_config_for_user(
    session: AsyncSession,
    *,
    telegram_id: int,
    name: str,
    volume_gb: float,
    validity_days: int,
    max_connections: int,
) -> ConfigOut:
    if sulgx_client is None:
        raise SulgXUnavailableError("اتصال به پنل SulgX تنظیم نشده است (SULGX_BASE_URL را بررسی کنید)")

    limit_bytes = int(volume_gb * (1024**3))

    try:
        panel_link: SulgXLink = await asyncio.to_thread(
            sulgx_client.create_link,
            label=name,
            limit_bytes=limit_bytes,
            max_connections=max_connections,
            expiry_days=validity_days,
        )
    except SulgXAPIError as exc:
        raise SulgXUnavailableError(f"خطا در ساخت کانفیگ روی پنل SulgX: {exc}") from exc

    if not panel_link.uid:
        raise SulgXUnavailableError("پنل SulgX هیچ uid برای لینک جدید برنگرداند")
    if not panel_link.link:
        raise SulgXUnavailableError(
            "پنل SulgX لینک VLESS را در پاسخ برنگرداند؛ مقدار SULGX_LINK_FIELD را در Environment Variables بررسی کنید"
        )

    expire_date = _parse_expires_at(panel_link.expires_at) or (
        dt.datetime.utcnow() + dt.timedelta(days=validity_days)
    )

    config = Config(
        telegram_id=telegram_id,
        name=name,
        uuid=panel_link.uid,
        volume_gb=volume_gb,
        used_volume_gb=panel_link.used_gb,
        max_connections=max_connections,
        validity_days=validity_days,
        link=panel_link.link,
        subscription_link=None,
        status=ConfigStatus.ACTIVE,
        expire_date=expire_date,
    )
    session.add(config)
    await session.flush()

    return _to_out(config)


async def _get_owned_config(session: AsyncSession, telegram_id: int, config_uuid: str) -> Config:
    result = await session.execute(
        select(Config).where(Config.telegram_id == telegram_id, Config.uuid == config_uuid)
    )
    config = result.scalar_one_or_none()
    if config is None:
        raise ConfigNotFoundError("کانفیگ مورد نظر پیدا نشد یا متعلق به شما نیست")
    return config


async def renew_config(
    session: AsyncSession,
    *,
    telegram_id: int,
    config_uuid: str,
    add_volume_gb: float | None,
    extend_days: int | None,
) -> ConfigOut:
    if sulgx_client is None:
        raise SulgXUnavailableError("اتصال به پنل SulgX تنظیم نشده است")

    config = await _get_owned_config(session, telegram_id, config_uuid)

    fields: dict = {}
    if add_volume_gb:
        fields["add_limit_bytes"] = int(add_volume_gb * (1024**3))
    if extend_days:
        fields["extend_days"] = extend_days

    try:
        panel_link = await asyncio.to_thread(sulgx_client.update_link, config.uuid, **fields)
    except SulgXAPIError as exc:
        raise SulgXUnavailableError(f"خطا در تمدید روی پنل SulgX: {exc}") from exc

    if add_volume_gb:
        config.volume_gb += add_volume_gb
    if extend_days:
        base = max(config.expire_date, dt.datetime.utcnow())
        config.expire_date = base + dt.timedelta(days=extend_days)
    if panel_link.link:
        config.link = panel_link.link
    config.status = ConfigStatus.ACTIVE

    await session.flush()
    return _to_out(config)


async def reset_config_link(session: AsyncSession, *, telegram_id: int, config_uuid: str) -> str:
    """تغییر UUID یک لینک از طریق endpoint واقعی POST /api/links/{uid}/new-uuid."""
    if sulgx_client is None:
        raise SulgXUnavailableError("اتصال به پنل SulgX تنظیم نشده است")

    config = await _get_owned_config(session, telegram_id, config_uuid)

    try:
        panel_link = await asyncio.to_thread(sulgx_client.rotate_uuid, config.uuid)
    except SulgXAPIError as exc:
        raise SulgXUnavailableError(f"خطا در تغییر UUID روی پنل SulgX: {exc}") from exc

    if not panel_link.uid or not panel_link.link:
        raise SulgXUnavailableError("پنل SulgX uid/لینک جدید را در پاسخ برنگرداند")

    config.uuid = panel_link.uid
    config.link = panel_link.link
    await session.flush()
    return panel_link.link


async def delete_config(session: AsyncSession, *, telegram_id: int, config_uuid: str) -> None:
    if sulgx_client is None:
        raise SulgXUnavailableError("اتصال به پنل SulgX تنظیم نشده است")

    config = await _get_owned_config(session, telegram_id, config_uuid)

    try:
        await asyncio.to_thread(sulgx_client.delete_link, config.uuid)
    except SulgXAPIError as exc:
        raise SulgXUnavailableError(f"خطا در حذف کانفیگ روی پنل SulgX: {exc}") from exc

    await session.delete(config)
    await session.flush()


async def sync_usage_from_panel(session: AsyncSession, *, telegram_id: int, config_uuid: str) -> ConfigOut:
    """
    حجم مصرف‌شده، حجم کل، تاریخ انقضا و وضعیت active را مستقیماً از پنل
    واقعی SulgX (GET /api/links) می‌خواند و رکورد محلی را به‌روز می‌کند.
    """
    if sulgx_client is None:
        raise SulgXUnavailableError("اتصال به پنل SulgX تنظیم نشده است")

    config = await _get_owned_config(session, telegram_id, config_uuid)

    try:
        panel_link = await asyncio.to_thread(sulgx_client.get_link, config.uuid)
    except SulgXAPIError as exc:
        raise SulgXUnavailableError(f"خطا در دریافت اطلاعات از پنل SulgX: {exc}") from exc

    if panel_link is None:
        # روی پنل دیگر وجود ندارد
        config.status = ConfigStatus.DELETED
        await session.flush()
        return _to_out(config)

    config.used_volume_gb = panel_link.used_gb
    if panel_link.limit_bytes:
        config.volume_gb = panel_link.limit_bytes / (1024**3)
    parsed_expiry = _parse_expires_at(panel_link.expires_at)
    if parsed_expiry:
        config.expire_date = parsed_expiry
    if panel_link.link:
        config.link = panel_link.link

    if config.expire_date <= dt.datetime.utcnow():
        config.status = ConfigStatus.EXPIRED
    elif not panel_link.active:
        config.status = ConfigStatus.DISABLED
    else:
        config.status = ConfigStatus.ACTIVE

    await session.flush()
    return _to_out(config)

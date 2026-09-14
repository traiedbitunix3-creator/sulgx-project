"""
بک‌اند FastAPI که Telegram Web App با آن صحبت می‌کند.
اجرای محلی: uvicorn backend.main:app --host 0.0.0.0 --port 8000
اجرای روی Railway (Start Command سرویس backend):
    uvicorn backend.main:app --host 0.0.0.0 --port $PORT
"""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

import logging

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.ext.asyncio import AsyncSession

from config import BASE_DIR, settings
from database.session import get_session, init_db

from backend.schemas import (
    ConfigCreateRequest,
    ConfigCreateResponse,
    ConfigDeleteRequest,
    ConfigRenewRequest,
    ConfigResetLinkRequest,
    UserConfigsResponse,
    UserProfileResponse,
)
from backend.security import TelegramAuthData, verify_telegram_init_data
from backend.services import config_service, user_service

logging.basicConfig(level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO))
logger = logging.getLogger("backend.main")

app = FastAPI(title="SulgX Bot Backend", version="1.1.0")

# -------------------------------------------------------------------------
# CORS
# -------------------------------------------------------------------------
# اگر WebApp از همان دامنه‌ی بک‌اند سرو شود (حالت پیش‌فرض این پروژه روی
# Railway، از طریق mount زیر روی /webapp) اصلاً نیازی به CORS نیست.
# CORSMiddleware فقط وقتی اضافه می‌شود که CORS_ORIGINS صراحتاً در
# Environment Variables ست شده باشد. "*" همراه با credentials=True در
# مرورگرها معتبر نیست، پس در آن حالت credentials غیرفعال می‌شود.
if settings.CORS_ORIGINS:
    allow_credentials = "*" not in settings.CORS_ORIGINS
    if not allow_credentials:
        logger.warning(
            "CORS_ORIGINS شامل '*' است؛ به همین دلیل allow_credentials خودکار غیرفعال شد "
            "(ترکیب wildcard origin با credentials در مرورگرها مجاز نیست)."
        )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=allow_credentials,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# -------------------------------------------------------------------------
# سرو کردن build شده‌ی Telegram WebApp (webapp/dist بعد از vite build)
# روی همان دامنه‌ی بک‌اند، زیر مسیر /webapp
# -------------------------------------------------------------------------
_WEBAPP_DIST = BASE_DIR / "webapp" / "dist"
if _WEBAPP_DIST.exists():
    app.mount("/webapp", StaticFiles(directory=str(_WEBAPP_DIST), html=True), name="webapp")


@app.on_event("startup")
async def on_startup() -> None:
    await init_db()
    logger.info("Backend started.")


# -------------------------------------------------------------------------
# Dependency: استخراج و اعتبارسنجی initData ارسالی از Web App
# -------------------------------------------------------------------------
async def get_current_telegram_user(request: Request) -> TelegramAuthData:
    init_data = request.headers.get("X-Telegram-Init-Data")
    if not init_data:
        raise HTTPException(status_code=401, detail="initData ارسال نشده است")

    auth_data = verify_telegram_init_data(
        init_data, settings.BOT_TOKEN, max_age_seconds=settings.TELEGRAM_INIT_DATA_MAX_AGE
    )
    if auth_data is None:
        raise HTTPException(status_code=401, detail="initData نامعتبر است")
    return auth_data


# -------------------------------------------------------------------------
# GET /user/profile
# -------------------------------------------------------------------------
@app.get("/user/profile", response_model=UserProfileResponse)
async def get_profile(
    auth: TelegramAuthData = Depends(get_current_telegram_user),
    session: AsyncSession = Depends(get_session),
):
    user = await user_service.get_or_create_user(session, auth)
    if user.is_banned:
        raise HTTPException(status_code=403, detail="حساب شما مسدود شده است")
    return UserProfileResponse(
        telegram_id=user.telegram_id,
        username=user.username,
        first_name=user.first_name,
        created_at=user.created_at,
    )


# -------------------------------------------------------------------------
# GET /user/configs
# -------------------------------------------------------------------------
@app.get("/user/configs", response_model=UserConfigsResponse)
async def get_configs(
    auth: TelegramAuthData = Depends(get_current_telegram_user),
    session: AsyncSession = Depends(get_session),
):
    configs = await config_service.list_user_configs(session, auth.user_id)
    return UserConfigsResponse(configs=configs)


# -------------------------------------------------------------------------
# POST /config/create
# -------------------------------------------------------------------------
@app.post("/config/create", response_model=ConfigCreateResponse)
async def create_config(
    payload: ConfigCreateRequest,
    auth: TelegramAuthData = Depends(get_current_telegram_user),
    session: AsyncSession = Depends(get_session),
):
    if not (settings.MIN_VOLUME_GB <= payload.volume_gb <= settings.MAX_VOLUME_GB):
        raise HTTPException(
            status_code=400,
            detail=f"حجم باید بین {settings.MIN_VOLUME_GB} تا {settings.MAX_VOLUME_GB} گیگابایت باشد",
        )
    if payload.validity_days not in settings.ALLOWED_VALIDITY_DAYS:
        raise HTTPException(status_code=400, detail="مدت زمان انتخابی مجاز نیست")
    if payload.max_connections not in settings.ALLOWED_MAX_CONNECTIONS:
        raise HTTPException(status_code=400, detail="تعداد دستگاه انتخابی مجاز نیست")

    try:
        config = await config_service.create_config_for_user(
            session,
            telegram_id=auth.user_id,
            name=payload.name,
            volume_gb=payload.volume_gb,
            validity_days=payload.validity_days,
            max_connections=payload.max_connections,
        )
    except config_service.SulgXUnavailableError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return ConfigCreateResponse(config=config)


# -------------------------------------------------------------------------
# POST /config/renew
# -------------------------------------------------------------------------
@app.post("/config/renew")
async def renew_config(
    payload: ConfigRenewRequest,
    auth: TelegramAuthData = Depends(get_current_telegram_user),
    session: AsyncSession = Depends(get_session),
):
    try:
        config = await config_service.renew_config(
            session,
            telegram_id=auth.user_id,
            config_uuid=payload.config_uuid,
            add_volume_gb=payload.add_volume_gb,
            extend_days=payload.extend_days,
        )
    except config_service.ConfigNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except config_service.SulgXUnavailableError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return {"success": True, "config": config}


# -------------------------------------------------------------------------
# POST /config/reset-link
# -------------------------------------------------------------------------
@app.post("/config/reset-link")
async def reset_link(
    payload: ConfigResetLinkRequest,
    auth: TelegramAuthData = Depends(get_current_telegram_user),
    session: AsyncSession = Depends(get_session),
):
    try:
        new_link = await config_service.reset_config_link(
            session, telegram_id=auth.user_id, config_uuid=payload.config_uuid
        )
    except config_service.ConfigNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except config_service.SulgXUnavailableError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return {"success": True, "link": new_link}


# -------------------------------------------------------------------------
# POST /config/delete
# -------------------------------------------------------------------------
@app.post("/config/delete")
async def delete_config(
    payload: ConfigDeleteRequest,
    auth: TelegramAuthData = Depends(get_current_telegram_user),
    session: AsyncSession = Depends(get_session),
):
    try:
        await config_service.delete_config(session, telegram_id=auth.user_id, config_uuid=payload.config_uuid)
    except config_service.ConfigNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except config_service.SulgXUnavailableError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return {"success": True}


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/")
async def root():
    return {"status": "ok", "service": "SulgX Bot Backend", "webapp": "/webapp/"}

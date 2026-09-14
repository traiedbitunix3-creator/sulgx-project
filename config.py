"""
تنظیمات مرکزی پروژه.
تمام مقادیر حساس فقط از Environment Variables خوانده می‌شوند (روی Railway:
Project -> Service -> Variables). هیچ Secretی نباید داخل کد یا .env کامیت‌شده
قرار بگیرد؛ فایل .env فقط برای اجرای محلی (local dev) است و در .gitignore
قرار دارد.
"""
import os
from pathlib import Path
from typing import List

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")  # روی Railway فایلی وجود ندارد و این خط بی‌اثر است


def _get_bool(key: str, default: bool = False) -> bool:
    return os.getenv(key, str(default)).strip().lower() in ("1", "true", "yes", "on")


def _get_list(key: str, sep: str = ",") -> List[str]:
    raw = os.getenv(key, "")
    return [item.strip() for item in raw.split(sep) if item.strip()]


def _get_int(key: str, default: int) -> int:
    try:
        return int(os.getenv(key, str(default)))
    except (TypeError, ValueError):
        return default


def _normalize_database_url(url: str) -> str:
    """
    Railway هنگام اتصال یک پلاگین PostgreSQL، متغیر DATABASE_URL را به‌صورت
    خودکار با اسکیم postgres:// یا postgresql:// تزریق می‌کند. SQLAlchemy
    async به درایور asyncpg نیاز دارد، پس اسکیم را به postgresql+asyncpg://
    تبدیل می‌کنیم. اگر مقدار از قبل درست بود یا sqlite بود، بدون تغییر
    برمی‌گردد.
    """
    if not url:
        return url
    if url.startswith("postgres://"):
        return "postgresql+asyncpg://" + url[len("postgres://"):]
    if url.startswith("postgresql://"):
        return "postgresql+asyncpg://" + url[len("postgresql://"):]
    return url


class Settings:
    # ---------------------------------------------------------------
    # Telegram Bot
    # ---------------------------------------------------------------
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
    BOT_USERNAME: str = os.getenv("BOT_USERNAME", "")

    # آی‌دی عددی ادمین‌های ربات (چند مقدار با کاما جدا می‌شود)
    ADMIN_IDS: List[int] = [int(x) for x in _get_list("ADMIN_IDS") if x.lstrip("-").isdigit()]

    # کانال‌های عضویت اجباری. فرمت هر آیتم: @username یا -100xxxxxxxxxx
    REQUIRED_CHANNELS: List[str] = _get_list("REQUIRED_CHANNELS")
    # لینک نمایشی هر کانال برای دکمه‌ها (به همان ترتیب REQUIRED_CHANNELS). اگر خالی باشد از t.me/username ساخته می‌شود.
    REQUIRED_CHANNELS_URLS: List[str] = _get_list("REQUIRED_CHANNELS_URLS")

    # ---------------------------------------------------------------
    # Web App (Telegram WebApp) — روی Railway توسط همین بک‌اند و زیر مسیر
    # /webapp سرو می‌شود (backend/main.py)
    # ---------------------------------------------------------------
    WEBAPP_URL: str = os.getenv("WEBAPP_URL", "https://example.up.railway.app/webapp/")

    # ---------------------------------------------------------------
    # Backend (FastAPI)
    # ---------------------------------------------------------------
    BACKEND_HOST: str = os.getenv("BACKEND_HOST", "0.0.0.0")
    # Railway پورت واقعی سرویس را در متغیر PORT تزریق می‌کند؛ برای اجرای
    # محلی از BACKEND_PORT (پیش‌فرض 8000) استفاده می‌شود.
    BACKEND_PORT: int = _get_int("PORT", 0) or _get_int("BACKEND_PORT", 8000)
    BACKEND_SECRET_KEY: str = os.getenv("BACKEND_SECRET_KEY", "change-me-please")

    # آدرس(های) مجاز برای CORS. اگر WebApp از همان دامنه‌ی بک‌اند سرو شود
    # (حالت پیش‌فرض این پروژه روی Railway) اصلاً نیازی به CORS نیست، پس
    # پیش‌فرض این مقدار خالی است (نه "*") تا با allow_credentials=True
    # ترکیب ناامنی ایجاد نشود. در صورت نیاز (مثلاً WebApp جدا هاست شود)
    # دامنه‌ها را در CORS_ORIGINS با کاما مشخص کنید.
    CORS_ORIGINS: List[str] = _get_list("CORS_ORIGINS")

    # حداکثر عمر مجاز initData ارسالی از Telegram WebApp (ثانیه)
    TELEGRAM_INIT_DATA_MAX_AGE: int = _get_int("TELEGRAM_INIT_DATA_MAX_AGE", 86400)

    # ---------------------------------------------------------------
    # Database (دیتابیس خودِ این پروژه - جدا از دیتابیس داخلی پنل SulgX)
    # روی Railway باید یک پلاگین PostgreSQL وصل شود؛ در آن صورت Railway
    # به‌صورت خودکار DATABASE_URL را ست می‌کند. برای اجرای محلی، در صورت
    # نبود DATABASE_URL، یک فایل SQLite موقت استفاده می‌شود.
    # ---------------------------------------------------------------
    DATABASE_URL: str = _normalize_database_url(
        os.getenv("DATABASE_URL", "").strip()
        or f"sqlite+aiosqlite:///{BASE_DIR / 'data' / 'bot.db'}"
    )

    # ---------------------------------------------------------------
    # SulgX Panel Connector
    # ---------------------------------------------------------------
    # آدرس ریشه‌ی پنل SulgX (بدون /panel در انتها). مثال روی Railway:
    # https://web-production-c666b.up.railway.app
    SULGX_BASE_URL: str = os.getenv("SULGX_BASE_URL", "").rstrip("/")
    SULGX_ADMIN_PASSWORD: str = os.getenv("SULGX_ADMIN_PASSWORD", "")
    SULGX_VERIFY_SSL: bool = _get_bool("SULGX_VERIFY_SSL", True)
    SULGX_REQUEST_TIMEOUT: int = _get_int("SULGX_REQUEST_TIMEOUT", 15)

    # ---------------------------------------------------------------
    # قوانین ساخت کانفیگ رایگان
    # ---------------------------------------------------------------
    MIN_VOLUME_GB: int = _get_int("MIN_VOLUME_GB", 1)
    MAX_VOLUME_GB: int = _get_int("MAX_VOLUME_GB", 55)
    ALLOWED_VALIDITY_DAYS: List[int] = [int(x) for x in _get_list("ALLOWED_VALIDITY_DAYS") or ["7", "15", "30"]]
    ALLOWED_MAX_CONNECTIONS: List[int] = [int(x) for x in _get_list("ALLOWED_MAX_CONNECTIONS") or ["1", "2", "3"]]

    # ---------------------------------------------------------------
    # لاگ
    # ---------------------------------------------------------------
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")


settings = Settings()

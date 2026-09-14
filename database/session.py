"""
مدیریت اتصال async به دیتابیس (SQLAlchemy).
این دیتابیس مختص خود پروژه (بات + بک‌اند) است و جدا از دیتابیس داخلی SulgX
Panel. روی Railway به‌صورت پیش‌فرض PostgreSQL استفاده می‌شود (از طریق
DATABASE_URL که با اتصال پلاگین Postgres به‌صورت خودکار تزریق می‌شود)؛
برای اجرای محلی بدون تنظیم DATABASE_URL، به SQLite موقت سقوط می‌کند.
"""
import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from config import settings

logger = logging.getLogger("database.session")

# مطمئن می‌شویم پوشه‌ی data برای فایل sqlite (فقط حالت local dev) وجود دارد
if settings.DATABASE_URL.startswith("sqlite"):
    db_path_str = settings.DATABASE_URL.split("///")[-1]
    Path(db_path_str).parent.mkdir(parents=True, exist_ok=True)
    _engine_kwargs = {}
else:
    # برای PostgreSQL (asyncpg) روی Railway: pool_pre_ping جلوی خطای
    # کانکشن‌های بسته‌شده توسط شبکه/دیتابیس را می‌گیرد و pool_recycle
    # از نگه‌داشتن کانکشن‌های خیلی قدیمی جلوگیری می‌کند.
    _engine_kwargs = {"pool_pre_ping": True, "pool_recycle": 1800}

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    future=True,
    **_engine_kwargs,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def init_db() -> None:
    """ساخت جدول‌ها در صورت عدم وجود. در استارتاپ بات و بک‌اند فراخوانی می‌شود."""
    from database.models import Base  # import محلی برای جلوگیری از circular import

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables ensured (init_db).")


@asynccontextmanager
async def get_session_ctx() -> AsyncIterator[AsyncSession]:
    """
    استفاده به‌صورت context manager:
        async with get_session_ctx() as session:
            ...
    """
    session = AsyncSessionLocal()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()


async def get_session() -> AsyncIterator[AsyncSession]:
    """
    Dependency برای FastAPI:
        async def endpoint(session: AsyncSession = Depends(get_session)):
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise

"""
نقطه ورود ربات تلگرام (aiogram 3, polling).
اجرا: python -m bot.main
"""
import asyncio
import logging
import sys
from pathlib import Path

# اجازه می‌دهد ماژول‌های ریشه پروژه (config, sulgx_api, database) import شوند
sys.path.append(str(Path(__file__).resolve().parent.parent))

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from config import settings
from database.session import init_db

from bot.handlers import admin as admin_handlers
from bot.handlers import config_flow as config_flow_handlers
from bot.handlers import service as service_handlers
from bot.handlers import start as start_handlers
from bot.middlewares.membership import MembershipMiddleware

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("bot.main")


async def main() -> None:
    if not settings.BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN در فایل .env تنظیم نشده است.")

    await init_db()

    bot = Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=MemoryStorage())

    # میدلور بررسی عضویت اجباری روی همه‌ی پیام‌ها و کال‌بک‌ها اعمال می‌شود،
    # به جز روی خود هندلر تایید عضویت (داخل middleware مدیریت می‌شود).
    dp.message.middleware(MembershipMiddleware())
    dp.callback_query.middleware(MembershipMiddleware())

    dp.include_router(start_handlers.router)
    dp.include_router(service_handlers.router)
    dp.include_router(config_flow_handlers.router)
    dp.include_router(admin_handlers.router)

    logger.info("Bot starting (polling mode)...")
    await bot.delete_webhook(drop_pending_updates=True)
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped.")

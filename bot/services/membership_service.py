"""
بررسی عضویت کاربر در کانال‌های اجباری با استفاده از bot.get_chat_member.
"""
import logging
from typing import List, Tuple

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest

from config import settings

logger = logging.getLogger("bot.services.membership")

NOT_MEMBER_STATUSES = {"left", "kicked"}


async def is_user_member(bot: Bot, chat_id: str, user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(chat_id=chat_id, user_id=user_id)
    except TelegramBadRequest as exc:
        # اگر ربات ادمین کانال نباشد یا chat_id اشتباه باشد، خطا می‌گیریم؛
        # برای جلوگیری از قفل‌شدن کامل کاربران، عضویت را نامعتبر در نظر می‌گیریم
        # ولی خطا را لاگ می‌کنیم تا ادمین متوجه شود.
        logger.warning("get_chat_member failed for %s / %s: %s", chat_id, user_id, exc)
        return False
    return member.status not in NOT_MEMBER_STATUSES


async def get_unjoined_channels(bot: Bot, user_id: int) -> List[Tuple[str, str]]:
    """
    برمی‌گرداند: لیستی از (chat_id, invite_url) کانال‌هایی که کاربر عضو نیست.
    """
    unjoined: List[Tuple[str, str]] = []
    channels = settings.REQUIRED_CHANNELS
    urls = settings.REQUIRED_CHANNELS_URLS

    for idx, chat_id in enumerate(channels):
        member_ok = await is_user_member(bot, chat_id, user_id)
        if not member_ok:
            if idx < len(urls) and urls[idx]:
                url = urls[idx]
            elif chat_id.startswith("@"):
                url = f"https://t.me/{chat_id.lstrip('@')}"
            else:
                url = "https://t.me/"
            unjoined.append((chat_id, url))

    return unjoined

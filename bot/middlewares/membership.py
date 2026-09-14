"""
میدلور بررسی عضویت اجباری کاربر در کانال‌های تعریف‌شده در .env (REQUIRED_CHANNELS)
پیش از پردازش هر پیام/کال‌بک. اگر عضو نباشد، پیام عضویت اجباری نمایش داده می‌شود
و پردازش هندلر اصلی متوقف می‌شود.
"""
import logging
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject

from config import settings
from bot.keyboards.membership import membership_required_keyboard
from bot.services.membership_service import get_unjoined_channels

logger = logging.getLogger("bot.middlewares.membership")

# callback_data هایی که حتی برای کاربران عضونشده هم باید پردازش شوند
# (مثلاً خودِ دکمه‌ی "عضو شدم")
ALLOWED_WITHOUT_MEMBERSHIP = {"check_membership"}


class MembershipMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        if not settings.REQUIRED_CHANNELS:
            return await handler(event, data)

        if isinstance(event, CallbackQuery) and event.data in ALLOWED_WITHOUT_MEMBERSHIP:
            return await handler(event, data)

        user = event.from_user
        if user is None:
            return await handler(event, data)

        bot = data["bot"]
        unjoined = await get_unjoined_channels(bot, user.id)

        if not unjoined:
            return await handler(event, data)

        text = (
            "🔐 برای استفاده از ربات ابتدا باید در کانال‌های زیر عضو شوید:\n\n"
            "📢 کانال‌های موردنیاز:"
        )
        keyboard = membership_required_keyboard(unjoined)

        if isinstance(event, Message):
            await event.answer(text, reply_markup=keyboard)
        elif isinstance(event, CallbackQuery):
            await event.answer("ابتدا باید در کانال‌ها عضو شوید ⛔️", show_alert=True)
            if event.message:
                await event.message.answer(text, reply_markup=keyboard)

        return None

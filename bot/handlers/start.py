import logging

from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.types import CallbackQuery, Message

from bot.keyboards.main_menu import main_menu_keyboard
from bot.services.membership_service import get_unjoined_channels
from bot.services import user_service

logger = logging.getLogger("bot.handlers.start")
router = Router(name="start")


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    user = message.from_user
    await user_service.get_or_create_user(user.id, user.username, user.first_name)

    if await user_service.is_banned(user.id):
        await message.answer("⛔️ حساب شما در ربات مسدود شده است.")
        return

    await message.answer(
        f"سلام {user.first_name} 👋\n\n"
        "به ربات SulgX خوش آمدید.\n"
        "از منوی زیر می‌توانید وارد پنل شخصی خود شوید یا کانفیگ رایگان دریافت کنید.",
        reply_markup=main_menu_keyboard(),
    )


@router.callback_query(F.data == "check_membership")
async def check_membership(callback: CallbackQuery) -> None:
    unjoined = await get_unjoined_channels(callback.bot, callback.from_user.id)
    if unjoined:
        await callback.answer("هنوز در همه‌ی کانال‌ها عضو نشده‌اید ⛔️", show_alert=True)
        return

    await callback.answer("✅ عضویت شما تایید شد")
    if callback.message:
        await callback.message.delete()
        await callback.message.answer(
            "✅ عضویت شما تایید شد.\nخوش آمدید!", reply_markup=main_menu_keyboard()
        )

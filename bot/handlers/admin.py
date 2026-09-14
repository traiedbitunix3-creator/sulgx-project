import asyncio
import logging

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from sqlalchemy import select

from config import settings
from bot.keyboards.main_menu import admin_menu_keyboard
from bot.services import user_service
from database.models import RequiredChannel
from database.session import get_session_ctx

logger = logging.getLogger("bot.handlers.admin")
router = Router(name="admin")


def is_admin(user_id: int) -> bool:
    return user_id in settings.ADMIN_IDS


class AdminStates(StatesGroup):
    waiting_ban_id = State()
    waiting_broadcast_text = State()
    waiting_channel_input = State()


@router.message(Command("admin"))
async def admin_panel(message: Message) -> None:
    if not is_admin(message.from_user.id):
        return
    await message.answer("🛠 پنل مدیریت", reply_markup=admin_menu_keyboard())


@router.callback_query(F.data == "admin:stats")
async def admin_stats(callback: CallbackQuery) -> None:
    if not is_admin(callback.from_user.id):
        await callback.answer("دسترسی ندارید ⛔️", show_alert=True)
        return
    total = await user_service.count_users()
    await callback.message.edit_text(
        f"📊 آمار کاربران\n\n👥 تعداد کل کاربران: {total}", reply_markup=admin_menu_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "admin:ban")
async def admin_ban_prompt(callback: CallbackQuery, state: FSMContext) -> None:
    if not is_admin(callback.from_user.id):
        await callback.answer("دسترسی ندارید ⛔️", show_alert=True)
        return
    await state.set_state(AdminStates.waiting_ban_id)
    await callback.message.edit_text("آی‌دی عددی کاربر برای بن/رفع‌بن را ارسال کنید:")
    await callback.answer()


@router.message(AdminStates.waiting_ban_id)
async def admin_ban_apply(message: Message, state: FSMContext) -> None:
    if not is_admin(message.from_user.id):
        return
    if not message.text or not message.text.strip("-").isdigit():
        await message.answer("آی‌دی نامعتبر است. دوباره ارسال کنید یا /admin بزنید.")
        return
    telegram_id = int(message.text.strip())
    ok = await user_service.ban_user(telegram_id, banned=True)
    await state.clear()
    if ok:
        await message.answer(f"✅ کاربر {telegram_id} بن شد.", reply_markup=admin_menu_keyboard())
    else:
        await message.answer("کاربر پیدا نشد.", reply_markup=admin_menu_keyboard())


@router.callback_query(F.data == "admin:broadcast")
async def admin_broadcast_prompt(callback: CallbackQuery, state: FSMContext) -> None:
    if not is_admin(callback.from_user.id):
        await callback.answer("دسترسی ندارید ⛔️", show_alert=True)
        return
    await state.set_state(AdminStates.waiting_broadcast_text)
    await callback.message.edit_text("متن پیام همگانی را ارسال کنید:")
    await callback.answer()


@router.message(AdminStates.waiting_broadcast_text)
async def admin_broadcast_send(message: Message, state: FSMContext) -> None:
    if not is_admin(message.from_user.id):
        return
    await state.clear()
    ids = await user_service.all_user_ids()
    success, failed = 0, 0
    status_msg = await message.answer(f"در حال ارسال به {len(ids)} کاربر ...")

    for uid in ids:
        try:
            await message.bot.send_message(uid, message.text)
            success += 1
        except Exception:
            failed += 1

    await status_msg.edit_text(
        f"📣 ارسال پایان یافت.\n✅ موفق: {success}\n❌ ناموفق: {failed}"
    )


@router.callback_query(F.data == "admin:channels")
async def admin_channels(callback: CallbackQuery) -> None:
    if not is_admin(callback.from_user.id):
        await callback.answer("دسترسی ندارید ⛔️", show_alert=True)
        return
    async with get_session_ctx() as session:
        result = await session.execute(select(RequiredChannel))
        channels = result.scalars().all()

    if not channels:
        text = "کانالی ثبت نشده است. برای افزودن، chat_id را در .env تنظیم کنید (REQUIRED_CHANNELS)."
    else:
        text = "📢 کانال‌های عضویت اجباری:\n\n" + "\n".join(
            f"- {c.chat_id} ({'فعال' if c.is_active else 'غیرفعال'})" for c in channels
        )
    await callback.message.edit_text(text, reply_markup=admin_menu_keyboard())
    await callback.answer()


@router.callback_query(F.data == "admin:panel_status")
async def admin_panel_status(callback: CallbackQuery) -> None:
    """وضعیت اتصال به پنل واقعی SulgX را نشان می‌دهد."""
    if not is_admin(callback.from_user.id):
        await callback.answer("دسترسی ندارید ⛔️", show_alert=True)
        return

    from sulgx_api import SulgXAPIError, sulgx_client

    if sulgx_client is None:
        text = "⚠️ SULGX_BASE_URL در Environment Variables تنظیم نشده است."
    else:
        try:
            await asyncio.to_thread(sulgx_client.check_connection)
            text = f"✅ اتصال به پنل SulgX برقرار است.\n🌐 آدرس: {sulgx_client.base_url}"
        except SulgXAPIError as exc:
            text = f"❌ اتصال به پنل SulgX ناموفق بود:\n{exc}"

    await callback.message.edit_text(text, reply_markup=admin_menu_keyboard())
    await callback.answer()

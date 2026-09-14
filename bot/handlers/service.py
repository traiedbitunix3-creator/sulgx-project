import datetime as dt

from aiogram import Router
from aiogram.types import Message

from bot.keyboards.main_menu import webapp_inline_keyboard
from bot.services import config_service

router = Router(name="service")


@router.message(lambda m: m.text == "📊 وضعیت سرویس")
async def show_service_status(message: Message) -> None:
    config = await config_service.get_latest_config(message.from_user.id)
    if config is None:
        await message.answer(
            "هنوز هیچ کانفیگی برای شما ساخته نشده است.\n"
            "از دکمه‌ی «🆕 دریافت کانفیگ رایگان» استفاده کنید."
        )
        return

    try:
        config = await config_service.sync_usage_from_panel(message.from_user.id, config.uuid)
    except config_service.SulgXUnavailableError:
        # در صورت در دسترس نبودن موقت پنل، آخرین اطلاعات ذخیره‌شده در دیتابیس نمایش داده می‌شود
        pass

    remaining = max(config.volume_gb - config.used_volume_gb, 0)
    is_active = config.expire_date > dt.datetime.utcnow() and config.status == "active"

    text = (
        f"📊 وضعیت سرویس: {'✅ فعال' if is_active else '❌ غیرفعال'}\n\n"
        f"👤 نام سرویس: {config.name}\n"
        f"🔋 حجم کل: {config.volume_gb:.1f} GB\n"
        f"📥 مصرف‌شده: {config.used_volume_gb:.1f} GB\n"
        f"💢 باقی‌مانده: {remaining:.1f} GB\n"
        f"📅 تاریخ انقضا: {config.expire_date.strftime('%Y-%m-%d')}\n"
        f"📶 آخرین اتصال: "
        f"{config.last_connection_at.strftime('%Y-%m-%d %H:%M') if config.last_connection_at else 'ثبت نشده'}"
    )

    await message.answer(text, reply_markup=webapp_inline_keyboard())

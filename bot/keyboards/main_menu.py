from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    WebAppInfo,
)

from config import settings


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🌐 ورود به پنل من", web_app=WebAppInfo(url=settings.WEBAPP_URL))],
            [KeyboardButton(text="📊 وضعیت سرویس"), KeyboardButton(text="🆕 دریافت کانفیگ رایگان")],
            [KeyboardButton(text="☎️ پشتیبانی")],
        ],
        resize_keyboard=True,
    )


def webapp_inline_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🌐 ورود به پنل من", web_app=WebAppInfo(url=settings.WEBAPP_URL))]
        ]
    )


def admin_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📊 آمار کاربران", callback_data="admin:stats")],
            [InlineKeyboardButton(text="📢 مدیریت کانال‌ها", callback_data="admin:channels")],
            [InlineKeyboardButton(text="🚫 بن کاربر", callback_data="admin:ban")],
            [InlineKeyboardButton(text="📣 پیام همگانی", callback_data="admin:broadcast")],
            [InlineKeyboardButton(text="🌐 وضعیت اتصال پنل", callback_data="admin:panel_status")],
        ]
    )

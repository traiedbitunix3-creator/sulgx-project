from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from config import settings


def volume_keyboard() -> InlineKeyboardMarkup:
    steps = [1, 5, 10, 20, 30, 55]
    steps = [v for v in steps if settings.MIN_VOLUME_GB <= v <= settings.MAX_VOLUME_GB]
    rows, row = [], []
    for v in steps:
        row.append(InlineKeyboardButton(text=f"{v} GB", callback_data=f"cfg:vol:{v}"))
        if len(row) == 3:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append([InlineKeyboardButton(text="❌ انصراف", callback_data="cfg:cancel")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def validity_keyboard() -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text=f"{d} روز", callback_data=f"cfg:days:{d}")]
        for d in settings.ALLOWED_VALIDITY_DAYS
    ]
    rows.append([InlineKeyboardButton(text="❌ انصراف", callback_data="cfg:cancel")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def devices_keyboard() -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text=f"{n} دستگاه", callback_data=f"cfg:dev:{n}")]
        for n in settings.ALLOWED_MAX_CONNECTIONS
    ]
    rows.append([InlineKeyboardButton(text="❌ انصراف", callback_data="cfg:cancel")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def confirm_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ ساخت کانفیگ", callback_data="cfg:confirm")],
            [InlineKeyboardButton(text="❌ انصراف", callback_data="cfg:cancel")],
        ]
    )

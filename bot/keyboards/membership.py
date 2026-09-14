from typing import List, Tuple

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def membership_required_keyboard(unjoined: List[Tuple[str, str]]) -> InlineKeyboardMarkup:
    rows = []
    for idx, (chat_id, url) in enumerate(unjoined, start=1):
        label = chat_id if chat_id.startswith("@") else f"کانال {idx}"
        rows.append([InlineKeyboardButton(text=f"📢 {label}", url=url)])

    rows.append([InlineKeyboardButton(text="✅ عضو شدم", callback_data="check_membership")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

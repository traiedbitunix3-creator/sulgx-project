import io

import qrcode
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import BufferedInputFile, CallbackQuery, Message

from bot.keyboards.config_flow import (
    confirm_keyboard,
    devices_keyboard,
    validity_keyboard,
    volume_keyboard,
)
from bot.keyboards.main_menu import main_menu_keyboard
from bot.services import config_service

router = Router(name="config_flow")


class ConfigFlow(StatesGroup):
    choosing_volume = State()
    choosing_validity = State()
    choosing_devices = State()
    confirming = State()


@router.message(lambda m: m.text == "🆕 دریافت کانفیگ رایگان")
async def start_config_flow(message: Message, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(ConfigFlow.choosing_volume)
    await message.answer("📦 حجم مورد نظر خود را انتخاب کنید:", reply_markup=volume_keyboard())


@router.callback_query(ConfigFlow.choosing_volume, F.data.startswith("cfg:vol:"))
async def choose_volume(callback: CallbackQuery, state: FSMContext) -> None:
    volume = int(callback.data.split(":")[-1])
    await state.update_data(volume_gb=volume)
    await state.set_state(ConfigFlow.choosing_validity)
    await callback.message.edit_text("⏳ مدت زمان اعتبار را انتخاب کنید:", reply_markup=validity_keyboard())
    await callback.answer()


@router.callback_query(ConfigFlow.choosing_validity, F.data.startswith("cfg:days:"))
async def choose_validity(callback: CallbackQuery, state: FSMContext) -> None:
    days = int(callback.data.split(":")[-1])
    await state.update_data(validity_days=days)
    await state.set_state(ConfigFlow.choosing_devices)
    await callback.message.edit_text("📱 تعداد دستگاه هم‌زمان را انتخاب کنید:", reply_markup=devices_keyboard())
    await callback.answer()


@router.callback_query(ConfigFlow.choosing_devices, F.data.startswith("cfg:dev:"))
async def choose_devices(callback: CallbackQuery, state: FSMContext) -> None:
    devices = int(callback.data.split(":")[-1])
    await state.update_data(max_connections=devices)
    data = await state.get_data()
    await state.set_state(ConfigFlow.confirming)

    text = (
        "🧾 خلاصه سفارش کانفیگ رایگان:\n\n"
        f"📦 حجم: {data['volume_gb']} GB\n"
        f"⏳ اعتبار: {data['validity_days']} روز\n"
        f"📱 تعداد دستگاه: {devices}\n\n"
        "برای ساخت نهایی تایید کنید."
    )
    await callback.message.edit_text(text, reply_markup=confirm_keyboard())
    await callback.answer()


@router.callback_query(ConfigFlow.confirming, F.data == "cfg:confirm")
async def confirm_config(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    await callback.message.edit_text("⏳ در حال ساخت کانفیگ روی پنل SulgX ...")

    try:
        config = await config_service.create_config(
            telegram_id=callback.from_user.id,
            name=f"user-{callback.from_user.id}",
            volume_gb=data["volume_gb"],
            validity_days=data["validity_days"],
            max_connections=data["max_connections"],
        )
    except config_service.SulgXUnavailableError as exc:
        await callback.message.edit_text(f"❌ خطا در ساخت کانفیگ:\n{exc}")
        await state.clear()
        await callback.answer()
        return

    await state.clear()
    await callback.message.edit_text(
        "✅ کانفیگ شما با موفقیت ساخته شد!\n\n"
        f"🔗 لینک VLESS:\n<code>{config.link}</code>\n\n"
        "کد QR در حال ارسال است ...",
    )

    qr_img = qrcode.make(config.link)
    buffer = io.BytesIO()
    qr_img.save(buffer, format="PNG")
    buffer.seek(0)

    await callback.message.answer_photo(
        BufferedInputFile(buffer.read(), filename="qr.png"),
        caption="📶 برای اتصال سریع، این QR را اسکن کنید.",
        reply_markup=main_menu_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data == "cfg:cancel")
async def cancel_config(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.edit_text("❌ عملیات لغو شد.")
    await callback.answer()

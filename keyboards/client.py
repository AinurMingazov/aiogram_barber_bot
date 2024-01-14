from datetime import datetime

from services.database_queries import find_free_slots
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup


async def get_time_slot_buttons(selected_date: datetime) -> InlineKeyboardMarkup:

    buttons = []
    slots = await find_free_slots(selected_date.date())
    keyboard_buttons = [InlineKeyboardButton(text=f"{slot}", callback_data=f"time_{slot}") for slot in slots]
    while keyboard_buttons:
        chunk = keyboard_buttons[:4]
        buttons.append(chunk)
        keyboard_buttons = keyboard_buttons[4:]
    return InlineKeyboardMarkup(inline_keyboard=buttons, hide=True)


async def get_confirm_choice_buttons() -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(text=f"{index}", callback_data=f"conf_{index}")
            for index in ["✅ Подтвердить", "❌ Отменить"]
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons, hide=True)


async def ask_user_phone() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True,
                               keyboard=[[KeyboardButton(text="📱 Отправить номер телефона", request_contact=True)]],)

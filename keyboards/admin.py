from datetime import datetime

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from handlers import AdminCallback
from services.database_queries import find_free_slots


async def get_admin_choice_buttons() -> InlineKeyboardMarkup:
    add_appointment = {"add_appointment": "Добавить запись", "add_day_off": "Добавить выходной"}
    show_appointment = {"all_appointments": "Посмотреть все записи", "day_appointments": "Посмотреть записи по дате"}

    buttons = [
        [
            InlineKeyboardButton(text=f"{name}", callback_data=AdminCallback(action=f"{title}").pack())
            for title, name in add_appointment.items()]
        ,
        [
            InlineKeyboardButton(text=f"{name}", callback_data=AdminCallback(action=f"{title}").pack())
            for title, name in show_appointment.items()
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons, hide=True)


async def get_admin_time_slot_buttons(selected_date: datetime) -> InlineKeyboardMarkup:

    buttons = []
    slots = await find_free_slots(selected_date.date())
    keyboard_buttons = [InlineKeyboardButton(
        text=f"{slot}", callback_data=AdminCallback(action=f"time_{str(slot.time.hour)}").pack()
    ) for slot in slots]
    while keyboard_buttons:
        chunk = keyboard_buttons[:4]
        buttons.append(chunk)
        keyboard_buttons = keyboard_buttons[4:]
    return InlineKeyboardMarkup(inline_keyboard=buttons, hide=True)


async def get_admin_confirm_choice_buttons() -> InlineKeyboardMarkup:
    confirm = {"1": "✅ Подтвердить", "0": "❌ Отменить"}
    buttons = [
        [
            InlineKeyboardButton(text=f"{answer}", callback_data=AdminCallback(action=f"conf_{key}").pack())
            for key, answer in confirm.items()
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons, hide=True)
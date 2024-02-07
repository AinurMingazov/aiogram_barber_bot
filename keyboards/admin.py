from datetime import datetime

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from handlers import AdminCallback
from services.time_slots import find_free_slots
from services.users import get_active_users


async def get_admin_choice_buttons() -> InlineKeyboardMarkup:
    add_appointment = {"add_appointment": "Добавить запись"}
    show_appointment = {"all_appointments": "Посмотреть все записи", "day_appointments": "Посмотреть записи по дате"}
    change_day = {"change_day": "Изменение дней", "edit_users": "Изменение клиентов"}

    buttons = [
        [
            InlineKeyboardButton(text=f"{name}", callback_data=AdminCallback(action=f"{title}").pack())
            for title, name in add_appointment.items()
        ],
        [
            InlineKeyboardButton(text=f"{name}", callback_data=AdminCallback(action=f"{title}").pack())
            for title, name in show_appointment.items()
        ],
        [
            InlineKeyboardButton(text=f"{name}", callback_data=AdminCallback(action=f"{title}").pack())
            for title, name in change_day.items()
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons, hide=True)


async def change_date_option(day_type) -> InlineKeyboardMarkup:
    date_options = {"make_fullwork": "Рабочий", "make_halfwork": "Не полный рабочий", "make_dayoff": "Выходной"}

    buttons = [
        [
            InlineKeyboardButton(text=f"{name}", callback_data=AdminCallback(action=f"{title}").pack())
            for title, name in date_options.items()
            if title.split("_")[1][0] != day_type.lower()[0]
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons, hide=True)


async def get_admin_time_slot_buttons(selected_date: datetime) -> InlineKeyboardMarkup:
    buttons = []
    slots = await find_free_slots(selected_date.date())
    keyboard_buttons = [
        InlineKeyboardButton(text=f"{slot}", callback_data=AdminCallback(action=f"time_{str(slot.time.hour)}").pack())
        for slot in slots
    ]
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


async def get_admin_clients_buttons() -> InlineKeyboardMarkup:
    users_buttons = {}
    users = await get_active_users()
    for user in users:
        users_buttons[user[0]] = [user[1], user[2]]

    buttons = [
        [
            InlineKeyboardButton(
                text=f"🧒 {user[1]} 📞 {user[0]}", callback_data=AdminCallback(action=f"id_{user_id}").pack()
            )
        ]
        for user_id, user in users_buttons.items()
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons, hide=True)

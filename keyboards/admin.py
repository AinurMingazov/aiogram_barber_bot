
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from handlers import AdminCallback


async def get_admin_choice_buttons() -> InlineKeyboardMarkup:
    add_appointment = {"add_appointment": "Добавить запись", "add_day_off": "Добавить выходной"}
    show_appointment = {"all_appointments": "Посмотреть все записи", "date_appointments": "Посмотреть записи по дате"}
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

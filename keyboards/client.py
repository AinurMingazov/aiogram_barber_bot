from services.database_queries import find_free_slots
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


async def get_time_slot_buttons(selected_date):

    buttons = []
    slots = await find_free_slots(selected_date.date())
    keyboard_buttons = [InlineKeyboardButton(text=f"{slot}", callback_data=f"time_{slot}") for slot in slots]
    while keyboard_buttons:
        chunk = keyboard_buttons[:4]
        buttons.append(chunk)
        keyboard_buttons = keyboard_buttons[4:]
    return InlineKeyboardMarkup(inline_keyboard=buttons, hide=True)

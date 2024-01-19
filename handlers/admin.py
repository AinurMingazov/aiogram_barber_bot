from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from aiogram.utils.markdown import hbold

from handlers import AdminCallback
from keyboards.admin import get_admin_choice_buttons
from services.database_queries import get_active_appointments

admin_router = Router()


@admin_router.message(Command("admin"))
async def command_admin(message: Message) -> None:

    keyboard = await get_admin_choice_buttons()
    await message.answer(
        f"🕹 Панель админа\n",
        reply_markup=keyboard,
        resize_keyboard=True,
    )


@admin_router.callback_query(AdminCallback.filter(F.action == "all_appointments"))
async def get_all_appointments(callback_query: CallbackQuery, callback_data: AdminCallback):
    active_appointments_by_dates = await get_active_appointments()
    for day, day_slots in active_appointments_by_dates.items():
        slots = []
        for slot in day_slots:
            slots.append(
                f' {slot["slot_time"].strftime("%H:%M")} 🧒 {slot["user_name"]} 📞 {slot["phone"]}\n'
            )

        await callback_query.message.edit_text(f" {hbold(day.strftime('%d %B %Y'))}\n {' '.join(slots)}")

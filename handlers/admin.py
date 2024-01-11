from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.utils.markdown import hbold

from services.database_queries import get_active_appointments

admin_router = Router()


@admin_router.message(Command("admin"))
async def command_admin(message: Message) -> None:
    # look all
    active_appointments_by_dates = await get_active_appointments()
    for day, day_slots in active_appointments_by_dates.items():
        slots = []
        for slot in day_slots:
            slots.append(
                f' {slot["slot_time"].strftime("%H:%M")} 🧒 {slot["user_name"]} 📞 {slot["phone"]}\n'
            )

        await message.answer(f" {hbold(day.strftime('%d %B %Y'))}\n {' '.join(slots)}")

    # add holiday
    # await message.answer(
    #     f"👋 функционал для администратора",
    # )

from datetime import datetime

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from aiogram.utils.markdown import hbold

from aiogram_calendar import SimpleCalendar, SimpleCalendarCallback
from config import some_redis
from handlers import AdminCallback
from handlers.client import answer_wrong_date
from keyboards.admin import get_admin_choice_buttons, get_admin_time_slot_buttons
from keyboards.client import get_time_slot_buttons, get_confirm_choice_buttons
from services.database_queries import get_active_appointments
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

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


@admin_router.callback_query(AdminCallback.filter(F.action == "add_appointment"))
async def add_appointment(callback_query: CallbackQuery, callback_data: AdminCallback):
    await callback_query.message.answer(
        f"🗓 Выберите желаемую дату для записи! \n"
        f"[1] - сегодня\n"
        f"∙2∙ - доступные даты\n"
        f"∶3∶ - запись завершена\n"
        f"⁝4⁝ - выходные\n",
        reply_markup=await SimpleCalendar().start_calendar(flag='admin'),
    )


@admin_router.callback_query(SimpleCalendarCallback.filter(F.flag == 'admin'))
async def get_appointment_day(callback_query: CallbackQuery, callback_data: SimpleCalendarCallback):
    calendar = SimpleCalendar(show_alerts=True)
    calendar.set_dates_range(datetime(2022, 1, 1), datetime(2025, 12, 31))
    is_selected, selected_date = await calendar.process_selection(callback_query, callback_data)

    if is_selected:
        selected_date_str = selected_date.strftime("%d %B %Y")
        some_redis[callback_query.message.chat.id] = {"on_date": selected_date_str}

        if selected_date.date() < datetime.now().date():
            await answer_wrong_date(
                callback_query,
                selected_date_str,
                "Нельзя выбрать прошедшую дату",
            )
        else:
            keyboard = await get_admin_time_slot_buttons(selected_date)
            await callback_query.message.edit_text(
                "🕛 Выберите свободное время",
                reply_markup=keyboard,
                resize_keyboard=True,
            )


@admin_router.callback_query(AdminCallback.filter(F.action.startswith("time_")))
async def set_appointment_time(callback_query: CallbackQuery, state: FSMContext, callback_data: AdminCallback):
    pass

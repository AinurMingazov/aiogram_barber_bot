from datetime import datetime

from aiogram import F, Router
from aiogram.types import CallbackQuery
from aiogram.utils.markdown import hbold

from aiogram_calendar import SimpleCalendar, SimpleCalendarCallback
from config import common_dates
from handlers import AdminCallback
from handlers.client import answer_wrong_date
from services.appointments import get_active_appointments

admin_get = Router()


@admin_get.callback_query(AdminCallback.filter(F.action == "all_appointments"))
async def get_all_appointments(callback_query: CallbackQuery, callback_data: AdminCallback):
    active_appointments_by_dates = await get_active_appointments()
    days = {}
    for day, day_slots in active_appointments_by_dates.items():
        slots = []
        for slot in day_slots:
            slots.append(f' {slot["slot_time"].strftime("%H:%M")} 🧒 {slot["user_name"]} 📞 {slot["phone"]}\n')
        days[day.strftime("%d %B %Y")] = " ".join(slots)

    answer = ""
    for day, add_appointments in days.items():
        answer += f"{hbold(day)}\n {add_appointments}\n\n"
    await callback_query.message.edit_text(answer)


@admin_get.callback_query(AdminCallback.filter(F.action == "day_appointments"))
async def get_day_appointments(callback_query: CallbackQuery, callback_data: AdminCallback):
    await callback_query.message.edit_text(
        "🗓 Выберите желаемую дату для просмотра записей! \n[1] - сегодня\n(2) - даты на которые есть запись\n",
        reply_markup=await SimpleCalendar().start_calendar(flag="day_admin"),
    )


@admin_get.callback_query(SimpleCalendarCallback.filter(F.flag == "day_admin"))
async def show_appointments_for_day(callback_query: CallbackQuery, callback_data: SimpleCalendarCallback):
    calendar = SimpleCalendar(show_alerts=True)
    calendar.set_dates_range(datetime(2022, 1, 1), datetime(2025, 12, 31))
    is_selected, selected_date = await calendar.process_selection(callback_query, callback_data)

    if is_selected:
        selected_date_str = selected_date.strftime("%d %B %Y")
        common_dates[callback_query.message.chat.id] = {"on_date": selected_date_str}

        if selected_date.date() < datetime.now().date():
            await answer_wrong_date(
                callback_query,
                selected_date_str,
                "Нельзя выбрать прошедшую дату",
            )
        else:
            active_appointments_for_date = await get_active_appointments(selected_date.date())
            days = {}
            for day, day_slots in active_appointments_for_date.items():
                slots = []
                for slot in day_slots:
                    slots.append(f' {slot["slot_time"].strftime("%H:%M")} 🧒 {slot["user_name"]} 📞 {slot["phone"]}\n')
                days[day.strftime("%d %B %Y")] = " ".join(slots)

            answer = ""
            for day, add_appointments in days.items():
                answer += f"{hbold(day)}\n {add_appointments}\n\n"
            await callback_query.message.edit_text(answer)

import json
from datetime import datetime

from aiogram import F, Router
from aiogram.types import CallbackQuery

from aiogram_calendar import SimpleCalendar, SimpleCalendarCallback
from config import admin_id
from constants import denotation_admin_days
from db.db_session import redis
from handlers import AdminCallback
from handlers.client import answer_wrong_date
from keyboards.admin import change_date_option
from models import CustomDay
from services.custom_days import create_or_update_custom_day, get_day_status

admin_edit_days = Router()


@admin_edit_days.callback_query(AdminCallback.filter(F.action == "change_day"))
async def choose_day(callback_query: CallbackQuery, callback_data: AdminCallback):
    await callback_query.message.edit_text(
        f"🗓 Выберите дату которую хотите сделать выходным!{denotation_admin_days}",
        reply_markup=await SimpleCalendar().start_calendar(flag="admin_edit_day"),
    )


@admin_edit_days.callback_query(SimpleCalendarCallback.filter(F.flag == "admin_edit_day"))
async def change_day_option(callback_query: CallbackQuery, callback_data: SimpleCalendarCallback):
    calendar = SimpleCalendar(show_alerts=True)
    calendar.set_dates_range(datetime(2022, 1, 1), datetime(2025, 12, 31))
    is_selected, selected_date, flag = await calendar.process_selection(callback_query, callback_data, "admin_edit_day")

    if is_selected:
        selected_date_str = selected_date.strftime("%d %B %Y")
        await redis.set(admin_id, json.dumps({callback_query.message.chat.id: {"change_day": selected_date_str}}))
        if selected_date.date() < datetime.now().date():
            await answer_wrong_date(
                callback_query,
                selected_date_str,
                "Нельзя выбрать прошедшую дату",
            )
        else:
            day_type = await get_day_status(selected_date.date())

            keyboard = await change_date_option(day_type)
            await callback_query.message.edit_text(
                f"👍 Выбрана {selected_date_str} сделать день", reply_markup=keyboard, resize_keyboard=True
            )


@admin_edit_days.callback_query(AdminCallback.filter(F.action.startswith("make_")))
async def get_day_option(callback_query: CallbackQuery):
    option = callback_query.data.split("_")[1]
    appointment_cache = json.loads(await redis.get(admin_id))
    selected_date_str = appointment_cache[str(callback_query.message.chat.id)]["change_day"]
    selected_date = datetime.strptime(selected_date_str, "%d %B %Y").date()

    if option == "fullwork":
        custom_day = CustomDay(date=selected_date, day_type="FULL_WORK")
        await create_or_update_custom_day(custom_day)
        await callback_query.message.edit_text(
            f"🕛 {selected_date_str} - сделан рабочим днем",
            resize_keyboard=True,
        )
    elif option == "halfwork":
        custom_day = CustomDay(date=selected_date, day_type="HALF_WORK")
        await create_or_update_custom_day(custom_day)
        await callback_query.message.edit_text(
            f"🕛 {selected_date_str} - сделан не полным рабочим днем",
            resize_keyboard=True,
        )
    elif option == "dayoff":
        custom_day = CustomDay(date=selected_date, day_type="DAY_OFF")
        await create_or_update_custom_day(custom_day)
        await callback_query.message.edit_text(
            f"🕛 {selected_date_str} - сделан выходным днем",
            resize_keyboard=True,
        )
    await redis.delete(callback_query.message.chat.id)

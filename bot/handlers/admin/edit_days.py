import json
from datetime import datetime, timedelta

from aiogram import F, Router
from aiogram.types import CallbackQuery

from api.models import CustomDay
from bot.aiogram_calendar.schemas import SimpleCalendarCallback
from bot.aiogram_calendar.simple_calendar import SimpleCalendar
from bot.config import calendar_dates_range, admin_id
from bot.constants import denotation_admin_days
from bot.handlers import AdminCallback
from bot.handlers.client import answer_wrong_date
from bot.keyboards.admin import change_date_option, get_admin_confirm_vacation
from bot.services.custom_days import get_day_status, create_or_update_custom_day
from db.db_session import redis

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
    calendar.set_dates_range(*calendar_dates_range)
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


@admin_edit_days.callback_query(AdminCallback.filter(F.action == "add_vacation"))
async def add_vacation(callback_query: CallbackQuery, callback_data: AdminCallback):
    await callback_query.message.edit_text(
        "🗓 Выберите первый день отпуска!",
        reply_markup=await SimpleCalendar().start_calendar(flag="admin_vacation_first_day"),
    )


@admin_edit_days.callback_query(SimpleCalendarCallback.filter(F.flag == "admin_vacation_first_day"))
async def set_vacation_first_day(callback_query: CallbackQuery, callback_data: SimpleCalendarCallback):
    calendar = SimpleCalendar(show_alerts=True)
    calendar.set_dates_range(*calendar_dates_range)
    is_selected, selected_date, flag = await calendar.process_selection(
        callback_query, callback_data, "admin_vacation_first_day"
    )

    if is_selected:
        selected_date_str = selected_date.strftime("%d %B %Y")
        await redis.set(callback_query.message.chat.id, json.dumps({"admin_vacation_first_day": selected_date_str}))
        if selected_date.date() < datetime.now().date():
            await answer_wrong_date(
                callback_query,
                selected_date_str,
                "Нельзя выбрать прошедшую дату",
            )
        else:
            await callback_query.message.edit_text(
                "🗓 Выберите последний день отпуска!",
                reply_markup=await SimpleCalendar().start_calendar(flag="admin_vacation_last_day"),
            )


@admin_edit_days.callback_query(SimpleCalendarCallback.filter(F.flag == "admin_vacation_last_day"))
async def set_vacation_last_day(callback_query: CallbackQuery, callback_data: SimpleCalendarCallback):
    calendar = SimpleCalendar(show_alerts=True)
    calendar.set_dates_range(*calendar_dates_range)
    is_selected, selected_date, flag = await calendar.process_selection(
        callback_query, callback_data, "admin_vacation_last_day"
    )

    if is_selected:
        selected_date_str = selected_date.strftime("%d %B %Y")
        days_cache = json.loads(await redis.get(callback_query.message.chat.id))
        days_cache["admin_vacation_last_day"] = selected_date_str
        await redis.set(callback_query.message.chat.id, json.dumps(days_cache))
        if selected_date.date() < datetime.now().date():
            await answer_wrong_date(
                callback_query,
                selected_date_str,
                "Нельзя выбрать прошедшую дату",
            )
        else:
            days_cache = json.loads(await redis.get(callback_query.message.chat.id))
            first_day = days_cache["admin_vacation_first_day"]
            keyboard = await get_admin_confirm_vacation()
            await callback_query.message.edit_text(
                f"👍 Подтвердите отпуск с {first_day} по {selected_date_str}",
                reply_markup=keyboard,
                resize_keyboard=True,
            )


@admin_edit_days.callback_query(AdminCallback.filter(F.action.startswith("confvac_")))
async def get_confirm(callback_query: CallbackQuery):
    confirm = callback_query.data.split("_")[1]
    if int(confirm):
        days_cache = json.loads(await redis.get(callback_query.message.chat.id))
        first_day = datetime.strptime(days_cache["admin_vacation_first_day"], "%d %B %Y").date()
        last_day = datetime.strptime(days_cache["admin_vacation_last_day"], "%d %B %Y").date()
        for dt in date_range(first_day, last_day):
            custom_day = CustomDay(date=dt, day_type="DAY_OFF")
            await create_or_update_custom_day(custom_day)
        await callback_query.message.edit_text(
            f"🎉 Отлично, Вы назначили себе отпуск с {days_cache['admin_vacation_first_day']} по {days_cache['admin_vacation_last_day']}",
            resize_keyboard=True,
        )
    else:
        await callback_query.message.edit_text("Вы отменили запись отпуска!")
    await redis.get(callback_query.message.chat.id)


def date_range(start_date, end_date):
    """Generate a range of dates between start_date and end_date."""
    delta = timedelta(days=1)
    current_date = start_date
    while current_date <= end_date:
        yield current_date
        current_date += delta

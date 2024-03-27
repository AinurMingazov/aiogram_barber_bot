import json
from datetime import datetime

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from aiogram_calendar import SimpleCalendar, SimpleCalendarCallback
from config import admin_id, bot
from constants import admin_canceled_appointment, admin_confirmed_appointment, denotation_admin_days
from db.db_session import redis
from handlers import AdminCallback
from handlers.client import answer_wrong_date
from keyboards.admin import change_date_option, get_admin_confirm_choice_buttons, get_admin_time_slot_buttons
from models import CustomDay
from services.appointments import add_admin_appointment, del_appointment, get_appointment, update_appointment
from services.custom_days import create_custom_day, get_day_status

admin_edit = Router()


class ClientForm(StatesGroup):
    name = State()


@admin_edit.callback_query(AdminCallback.filter(F.action == "add_appointment"))
async def add_appointment(callback_query: CallbackQuery, callback_data: AdminCallback):
    await callback_query.message.edit_text(
        f"🗓 Выберите желаемую дату для записи! {denotation_admin_days}",
        reply_markup=await SimpleCalendar().start_calendar(flag="admin"),
    )


@admin_edit.callback_query(SimpleCalendarCallback.filter(F.flag == "admin"))
async def get_appointment_day(callback_query: CallbackQuery, callback_data: SimpleCalendarCallback):
    calendar = SimpleCalendar(show_alerts=True)
    calendar.set_dates_range(datetime(2022, 1, 1), datetime(2025, 12, 31))
    is_selected, selected_date = await calendar.process_selection(callback_query, callback_data)

    if is_selected:
        selected_date_str = selected_date.strftime("%d %B %Y")
        await redis.set(callback_query.message.chat.id, json.dumps({"on_date": selected_date_str}))
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


@admin_edit.callback_query(AdminCallback.filter(F.action.startswith("time_")))
async def set_appointment_time(callback_query: CallbackQuery, state: FSMContext, callback_data: AdminCallback):
    selected_time_str = callback_query.data.split("_")[1] + ":00"
    appointment_cache = json.loads(await redis.get(callback_query.message.chat.id))
    appointment_cache["on_time"] = selected_time_str
    await redis.set(callback_query.message.chat.id, json.dumps(appointment_cache))
    await state.set_state(ClientForm.name)
    await callback_query.message.edit_text("Напиши имя клиента")


@admin_edit.message(ClientForm.name)
async def process_name(message: Message, state: FSMContext) -> None:
    keyboard = await get_admin_confirm_choice_buttons()
    appointment_cache = json.loads(await redis.get(message.chat.id))
    appointment_cache["user_name"] = message.text
    await redis.set(message.chat.id, json.dumps(appointment_cache))
    await message.answer(
        f"👍 Записать клиента {message.text}\n 🗓 Дата:"
        f" {appointment_cache['on_date']}\n ⌚ Время: {appointment_cache['on_time']}",
        reply_markup=keyboard,
        resize_keyboard=True,
    )
    await state.update_data(name=message.text)
    await state.clear()


@admin_edit.callback_query(AdminCallback.filter(F.action.startswith("conf_")))
async def get_confirm(callback_query: CallbackQuery):
    confirm = callback_query.data.split("_")[1]
    if int(confirm):
        appointment_cache = json.loads(await redis.get(callback_query.message.chat.id))
        await add_admin_appointment(callback_query.message)
        await callback_query.message.edit_text(
            f"🎉 Отлично, Вы записали клиента {appointment_cache['user_name']}\nДату: {appointment_cache['on_date']}\n"
            f"Время: {appointment_cache['on_time']}!\n",
            resize_keyboard=True,
        )
    else:
        await callback_query.message.edit_text("Вы отменили запись!")
    await redis.get(callback_query.message.chat.id)


@admin_edit.callback_query(AdminCallback.filter(F.action == "change_day"))
async def add_day_off(callback_query: CallbackQuery, callback_data: AdminCallback):
    await callback_query.message.edit_text(
        f"🗓 Выберите дату которую хотите сделать выходным!{denotation_admin_days}",
        reply_markup=await SimpleCalendar().start_calendar(flag="admin_off"),
    )


@admin_edit.callback_query(SimpleCalendarCallback.filter(F.flag == "admin_off"))
async def change_day_option(callback_query: CallbackQuery, callback_data: SimpleCalendarCallback):
    calendar = SimpleCalendar(show_alerts=True)
    calendar.set_dates_range(datetime(2022, 1, 1), datetime(2025, 12, 31))
    is_selected, selected_date = await calendar.process_selection(callback_query, callback_data)

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


@admin_edit.callback_query(AdminCallback.filter(F.action.startswith("make_")))
async def get_day_option(callback_query: CallbackQuery):
    option = callback_query.data.split("_")[1]
    appointment_cache = json.loads(await redis.get(admin_id))
    selected_date_str = appointment_cache[str(callback_query.message.chat.id)]["change_day"]
    selected_date = datetime.strptime(selected_date_str, "%d %B %Y").date()

    if option == "fullwork":
        custom_day = CustomDay(date=selected_date, day_type="DAY_OFF")
        await create_custom_day(custom_day)
        await callback_query.message.edit_text(
            f"🕛 {selected_date_str} - сделан рабочим днем",
            resize_keyboard=True,
        )
    elif option == "halfwork":
        custom_day = CustomDay(date=selected_date, day_type="HALF_WORKDAY")
        await create_custom_day(custom_day)
        await callback_query.message.edit_text(
            f"🕛 {selected_date_str} - сделан не полным рабочим днем",
            resize_keyboard=True,
        )
    elif option == "dayoff":
        custom_day = CustomDay(date=selected_date, day_type="DAY_OFF")
        await create_custom_day(custom_day)
        await callback_query.message.edit_text(
            f"🕛 {selected_date_str} - сделан выходным днем",
            resize_keyboard=True,
        )
    await redis.delete(callback_query.message.chat.id)


@admin_edit.callback_query(AdminCallback.filter(F.action.startswith("ap-conf_")))
async def get_confirm_appointment(callback_query: CallbackQuery):
    answer = callback_query.data.split("_")
    confirm, user_id = answer[1], answer[2]
    appointment_cache = json.loads(await redis.get(admin_id))
    appointment_id = appointment_cache.get(int(user_id), None).get("confirm_appointment", None)
    if int(confirm):
        await callback_query.message.edit_text(
            "🎉 Вы записали клиента",
            resize_keyboard=True,
        )
        updated_params = {"is_approved": True}
        await update_appointment(appointment_id, **updated_params)
        await send_appointment_status(user_id, appointment_id, True)
    else:
        await callback_query.message.edit_text("Вы отменили запись!")
        await send_appointment_status(user_id, appointment_id, False)
        await del_appointment(appointment_id)
    await redis.delete(callback_query.message.chat.id)


async def send_appointment_status(user_id, appointment_id, status):
    appointment = await get_appointment(appointment_id)
    if status:
        answer = admin_confirmed_appointment
    else:
        answer = admin_canceled_appointment
    await bot.send_message(
        user_id, f"Ваша запись на\n" f"Дату: {appointment.date} - Время: {appointment.time}!\n{answer}"
    )

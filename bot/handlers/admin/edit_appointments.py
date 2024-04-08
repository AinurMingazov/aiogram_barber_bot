import json
from datetime import datetime

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from bot.aiogram_calendar.schemas import SimpleCalendarCallback
from bot.aiogram_calendar.simple_calendar import SimpleCalendar
from bot.config import calendar_dates_range, admin_id, bot
from bot.constants import denotation_admin_days, admin_confirmed_appointment, admin_canceled_appointment
from bot.handlers import AdminCallback
from bot.handlers.client import answer_wrong_date
from bot.keyboards.admin import get_admin_time_slot_buttons, get_admin_confirm_choice_buttons
from bot.services.appointments import add_admin_appointment, update_appointment, del_appointment, get_appointment
from db.db_session import redis

admin_edit = Router()


class ClientForm(StatesGroup):
    name = State()


@admin_edit.callback_query(AdminCallback.filter(F.action == "add_appointment"))
async def add_appointment(callback_query: CallbackQuery, callback_data: AdminCallback):
    await callback_query.message.edit_text(
        f"🗓 Выберите желаемую дату для записи! {denotation_admin_days}",
        reply_markup=await SimpleCalendar().start_calendar(flag="admin_appointment"),
    )


@admin_edit.callback_query(SimpleCalendarCallback.filter(F.flag == "admin_appointment"))
async def get_appointment_day(callback_query: CallbackQuery, callback_data: SimpleCalendarCallback):
    calendar = SimpleCalendar(show_alerts=True)
    calendar.set_dates_range(*calendar_dates_range)
    is_selected, selected_date, flag = await calendar.process_selection(
        callback_query, callback_data, "admin_appointment"
    )

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


@admin_edit.callback_query(AdminCallback.filter(F.action.startswith("ap-conf_")))
async def get_confirm_appointment(callback_query: CallbackQuery):
    answer = callback_query.data.split("_")
    confirm, user_id = answer[1], answer[2]
    appointment_cache = json.loads(await redis.get(admin_id))
    appointment_id = appointment_cache.get(user_id, None).get("confirm_appointment", None)
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

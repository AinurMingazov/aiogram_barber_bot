from datetime import datetime

from aiogram import Router, F
from aiogram.types import CallbackQuery, Message

from aiogram_calendar import SimpleCalendar, SimpleCalendarCallback
from config import some_redis
from constants import denotation_admin_days
from handlers import AdminCallback
from handlers.client import answer_wrong_date
from keyboards.admin import get_admin_time_slot_buttons, get_admin_confirm_choice_buttons, change_date_option
from models import CustomDay
from services.appointments import add_admin_appointment
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

from services.database_queries import create_custom_day

admin_edit = Router()


class ClientForm(StatesGroup):
    name = State()


@admin_edit.callback_query(AdminCallback.filter(F.action == "add_appointment"))
async def add_appointment(callback_query: CallbackQuery, callback_data: AdminCallback):
    await callback_query.message.edit_text(
        f"🗓 Выберите желаемую дату для записи! {denotation_admin_days}",
        reply_markup=await SimpleCalendar().start_calendar(flag='admin'),
    )


@admin_edit.callback_query(SimpleCalendarCallback.filter(F.flag == 'admin'))
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


@admin_edit.callback_query(AdminCallback.filter(F.action.startswith("time_")))
async def set_appointment_time(callback_query: CallbackQuery, state: FSMContext, callback_data: AdminCallback):
    selected_time_str = callback_query.data.split("_")[1]+':00'
    some_redis[callback_query.message.chat.id]["on_time"] = selected_time_str
    await state.set_state(ClientForm.name)
    await callback_query.message.edit_text('Напиши имя клиента')


@admin_edit.message(ClientForm.name)
async def process_name(message: Message, state: FSMContext) -> None:
    keyboard = await get_admin_confirm_choice_buttons()
    some_redis[message.chat.id]["user_name"] = message.text
    await message.answer(
        f"👍 Записать клиента {message.text}\n 🗓 Дата:"
        f" {some_redis[message.chat.id]['on_date']}\n ⌚ Время: {some_redis[message.chat.id]['on_time']}",
        reply_markup=keyboard,
        resize_keyboard=True,
    )
    await state.update_data(name=message.text)
    await state.clear()


@admin_edit.callback_query(AdminCallback.filter(F.action.startswith("conf_")))
async def get_confirm(callback_query: CallbackQuery):
    confirm = callback_query.data.split("_")[1]
    if int(confirm):
        await add_admin_appointment(callback_query.message)
        await callback_query.message.edit_text(
            f"🎉 Отлично, Вы записали клиента {some_redis[callback_query.message.chat.id]['user_name']}\nДату: {some_redis[callback_query.message.chat.id]['on_date']}\n"
            f"Время: {some_redis[callback_query.message.chat.id]['on_time']}!\n",
            resize_keyboard=True,
        )
    else:
        await callback_query.message.edit_text("Вы отменили запись!")
    del some_redis[callback_query.message.chat.id]


@admin_edit.callback_query(AdminCallback.filter(F.action == "change_day"))
async def add_day_off(callback_query: CallbackQuery, callback_data: AdminCallback):
    await callback_query.message.edit_text(
        f"🗓 Выберите дату которую хотите сделать выходным!{denotation_admin_days}",
        reply_markup=await SimpleCalendar().start_calendar(flag='admin_off'),
    )


@admin_edit.callback_query(SimpleCalendarCallback.filter(F.flag == 'admin_off'))
async def change_day_option(callback_query: CallbackQuery, callback_data: SimpleCalendarCallback):
    calendar = SimpleCalendar(show_alerts=True)
    calendar.set_dates_range(datetime(2022, 1, 1), datetime(2025, 12, 31))
    is_selected, selected_date = await calendar.process_selection(callback_query, callback_data)

    if is_selected:
        selected_date_str = selected_date.strftime("%d %B %Y")
        some_redis[callback_query.message.chat.id] = {}
        some_redis[callback_query.message.chat.id]["change_day"] = selected_date
        if selected_date.date() < datetime.now().date():
            await answer_wrong_date(
                callback_query,
                selected_date_str,
                "Нельзя выбрать прошедшую дату",
            )
        else:
            # add check day option
            keyboard = await change_date_option()
            await callback_query.message.edit_text(
                f"👍 Выбрана {selected_date_str} сделать день",
                reply_markup=keyboard,
                resize_keyboard=True)


@admin_edit.callback_query(AdminCallback.filter(F.action.startswith("make_")))
async def get_day_option(callback_query: CallbackQuery):
    option = callback_query.data.split("_")[1]

    selected_date = some_redis[callback_query.message.chat.id]["change_day"]
    selected_date_str = selected_date.strftime("%d %B %Y")

    if option == "fullwork":
        custom_day = CustomDay(
            date=selected_date.date(),
            day_type='DAY_OFF'
        )
        await create_custom_day(custom_day)
        await callback_query.message.edit_text(
            f"🕛 {selected_date_str} - сделан рабочим днем",
            resize_keyboard=True,
        )
    elif option == "halfwork":
        custom_day = CustomDay(
            date=selected_date.date(),
            day_type='HALF_WORKDAY'
        )
        await create_custom_day(custom_day)
        await callback_query.message.edit_text(
            f"🕛 {selected_date_str} - сделан не полным рабочим днем",
            resize_keyboard=True,
        )
    elif option == "dayoff":
        custom_day = CustomDay(
            date=selected_date.date(),
            day_type='DAY_OFF'
        )
        await create_custom_day(custom_day)
        await callback_query.message.edit_text(
            f"🕛 {selected_date_str} - сделан выходным днем",
            resize_keyboard=True,
        )
    del some_redis[callback_query.message.chat.id]

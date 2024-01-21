from datetime import datetime

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from aiogram.utils.markdown import hbold

from aiogram_calendar import SimpleCalendar, SimpleCalendarCallback
from config import some_redis
from handlers import AdminCallback
from handlers.client import answer_wrong_date
from keyboards.admin import get_admin_choice_buttons, get_admin_time_slot_buttons, get_admin_confirm_choice_buttons
from services.appointments import add_admin_appointment
from services.database_queries import get_active_appointments
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

admin_router = Router()


class ClientForm(StatesGroup):
    name = State()


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
    days = {}
    for day, day_slots in active_appointments_by_dates.items():
        slots = []
        for slot in day_slots:
            slots.append(
                f' {slot["slot_time"].strftime("%H:%M")} 🧒 {slot["user_name"]} 📞 {slot["phone"]}\n'
            )
        days[day.strftime('%d %B %Y')] = ' '.join(slots)

    answer = ''
    for day, add_appointments in days.items():
        answer += f"{hbold(day)}\n {add_appointments}\n\n"
    await callback_query.message.edit_text(answer)


@admin_router.callback_query(AdminCallback.filter(F.action == "add_appointment"))
async def add_appointment(callback_query: CallbackQuery, callback_data: AdminCallback):
    await callback_query.message.edit_text(
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
    selected_time_str = callback_query.data.split("_")[1]+':00'
    some_redis[callback_query.message.chat.id]["on_time"] = selected_time_str
    await state.set_state(ClientForm.name)
    await callback_query.message.edit_text('Напиши имя клиента')


@admin_router.message(ClientForm.name)
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


@admin_router.callback_query(AdminCallback.filter(F.action.startswith("conf_")))
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


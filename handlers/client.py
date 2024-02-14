from datetime import datetime

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message, ReplyKeyboardRemove
from aiogram.utils.markdown import hbold

from aiogram_calendar import SimpleCalendar, SimpleCalendarCallback
from config import admin_id, bot, some_redis
from constants import denotation_client_days
from keyboards.admin import approve_appointment_keyboard
from keyboards.client import ask_user_phone, get_confirm_choice_buttons, get_time_slot_buttons
from services.appointments import add_appointment, get_appointment
from services.calendar_days import get_available_days, get_days_off
from services.custom_days import get_admin_date_off, get_unavailable_days
from services.users import get_bar_user_phone_number, get_user_have_active_appointment, update_bar_user

client_router = Router()


@client_router.message(Command("help"))
async def command_help(message: Message) -> None:
    await message.answer(f"👋 Добрый день, {hbold(message.from_user.full_name)}!{denotation_client_days}")


@client_router.message(Command("start"))
async def command_start_handler(message: Message) -> None:
    """
    This handler receives messages with `/start` command
    """
    unavailable_days = await get_unavailable_days()
    some_redis["unavailable_days"] = unavailable_days

    admin_date_off = await get_admin_date_off()
    some_redis["admin_date_off"] = admin_date_off

    user_have_active_appointment = await get_user_have_active_appointment(message.from_user.id)
    if user_have_active_appointment:
        await message.answer(
            f"🎉 Вы записаны, ждем Вас! \nДата: {user_have_active_appointment[0].strftime('%d %B %Y')}"
            f"\nВремя: {user_have_active_appointment[1].strftime('%H:%M')} !\n"
            f"📍 Нельзя записаться 2 раза",
            resize_keyboard=True,
        )
    else:
        await message.answer(
            f"👋 Добрый день, {hbold(message.from_user.full_name)}! \n"
            f"🗓 Выберите желаемую дату для записи!{denotation_client_days}",
            reply_markup=await SimpleCalendar().start_calendar(),
        )


@client_router.callback_query(SimpleCalendarCallback.filter(F.flag == "user"))
async def get_day_simple_calendar(callback_query: CallbackQuery, callback_data: SimpleCalendarCallback):
    unavailable_days = await get_unavailable_days()
    days_off = get_days_off()
    available_days = get_available_days()

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
        elif selected_date.date() in days_off:
            await answer_wrong_date(
                callback_query,
                selected_date_str,
                "К сожалению, это выходной",
            )
        elif selected_date.date() in unavailable_days:
            await answer_wrong_date(
                callback_query,
                selected_date_str,
                "К сожалению, на этот день запись уже закрыта",
            )
        elif selected_date.date() not in available_days:
            await answer_wrong_date(
                callback_query,
                selected_date_str,
                "К сожалению, запись на далекое будущее не делаем",
            )
        else:
            keyboard = await get_time_slot_buttons(selected_date)
            await callback_query.message.edit_text(
                "🕛 Выберите свободное время",
                reply_markup=keyboard,
                resize_keyboard=True,
            )


async def answer_wrong_date(callback_query: CallbackQuery, selected_date_str: str, answer: str):
    await callback_query.message.answer(
        f"⛔ Вы выбрали {selected_date_str}\n{answer}, повторите выбор",
        reply_markup=await SimpleCalendar().start_calendar(),
    )


@client_router.callback_query(lambda query: query.data.startswith("time_"))
async def get_time(callback_query: CallbackQuery):
    selected_time_str = callback_query.data.split("_")[1]
    some_redis[callback_query.message.chat.id]["on_time"] = selected_time_str
    keyboard = await get_confirm_choice_buttons()
    await callback_query.message.edit_text(
        f"👍 Отлично, подтвердите запись на\n 🗓 Дата:"
        f" {some_redis[callback_query.message.chat.id]['on_date']}\n ⌚ Время: {some_redis[callback_query.message.chat.id]['on_time']}",
        reply_markup=keyboard,
        resize_keyboard=True,
    )


@client_router.callback_query(lambda query: query.data.startswith("conf_"))
async def get_confirm(callback_query: CallbackQuery):
    confirm = callback_query.data.split("_")[1]
    if confirm.lower() == "✅ подтвердить":
        bar_user_id, appointment_id = await add_appointment(callback_query.message)

        await callback_query.message.edit_text(
            f"🎉 Отлично, Вы записаны на\nДату: {some_redis[callback_query.message.chat.id]['on_date']}\n"
            f"Время: {some_redis[callback_query.message.chat.id]['on_time']}!\n"
            f"Мы отправим сообщение об подтверждении заявки от администратора",
            resize_keyboard=True,
        )
        appointment = await get_appointment(appointment_id)
        appointment_keyboard = await approve_appointment_keyboard()
        await bot.send_message(
            int(admin_id),
            f"Подтверди запись\n{appointment.name} записался на\n"
            f"Дату: {appointment.date} - Время: {appointment.time}!\n",
            reply_markup=appointment_keyboard,
        )

        user_phone_number = await get_bar_user_phone_number(bar_user_id)
        if not user_phone_number:
            markup = await ask_user_phone()
            await callback_query.message.answer(
                "Отправьте номер телефона для возможности с Вами связаться",
                resize_keyboard=True,
                reply_markup=markup,
            )
    else:
        await callback_query.message.edit_text("Вы отменили запись!")
    del some_redis[callback_query.message.chat.id]


@client_router.message(F.contact)
async def func_contact(message: Message):
    updated_user_params = {"phone": message.contact.phone_number}
    await update_bar_user(message.chat.id, **updated_user_params)
    await message.answer(
        "Спасибо, Ваш номер сохранен!",
        resize_keyboard=True,
        reply_markup=ReplyKeyboardRemove(),
    )
    await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)

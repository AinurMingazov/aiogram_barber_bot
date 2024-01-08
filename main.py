import asyncio
import os
from datetime import datetime

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandStart
from aiogram.filters.callback_data import CallbackData
from aiogram.types import (CallbackQuery, InlineKeyboardButton,
                           InlineKeyboardMarkup, KeyboardButton, Message,
                           ReplyKeyboardMarkup, ReplyKeyboardRemove)
from aiogram.utils.markdown import hbold

from aiogram_calendar import SimpleCalendar, SimpleCalendarCallback
from constants import some_redis
from models import Appointment, BarUser
from services.database_queries import (create_appointment,
                                       create_or_get_bar_user, find_free_slots,
                                       get_active_appointments,
                                       get_available_days,
                                       get_bar_user_phone_number, get_days_off,
                                       get_time_slot_id, get_unavailable_days,
                                       get_user_have_active_appointment,
                                       update_bar_user)

bot = Bot(token=os.getenv("BBOT_TOKEN", ""), parse_mode="HTML")
# Bot
dp = Dispatcher()


@dp.message(Command("admin"))
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


@dp.message(Command("help"))
async def command_help(message: Message) -> None:
    await message.answer(
        f"👋 Добрый день, {hbold(message.from_user.full_name)}! \n"
        f"🗓 При выборе даты есть такие подсказки! \n"
        f"[1] - сегодня\n"
        f"∙2∙ - доступные даты\n"
        f"∶3∶ - запись завершена\n"
        f"⁝4⁝ - выходные\n"
        f" 5 - обычные даты на которые запись не ведется",
    )


@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    """
    This handler receives messages with `/start` command
    """
    unavailable_days = await get_unavailable_days()
    some_redis["unavailable_days"] = unavailable_days
    user_have_active_appointment = await get_user_have_active_appointment(
        message.from_user.id
    )
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
            f"🗓 Выберите желаемую дату для записи! \n"
            f"[1] - сегодня\n"
            f"∙2∙ - доступные даты\n"
            f"∶3∶ - запись завершена\n"
            f"⁝4⁝ - выходные\n"
            f" 5 - обычные даты на которые запись не ведется",
            reply_markup=await SimpleCalendar().start_calendar(),
        )


@dp.callback_query(SimpleCalendarCallback.filter())
async def get_day_simple_calendar(
    callback_query: CallbackQuery, callback_data: CallbackData
):
    unavailable_days = await get_unavailable_days()
    days_off = get_days_off()
    available_days = get_available_days()
    calendar = SimpleCalendar(show_alerts=True)
    calendar.set_dates_range(datetime(2022, 1, 1), datetime(2025, 12, 31))
    is_selected, selected_date = await calendar.process_selection(
        callback_query, callback_data
    )

    if is_selected:
        selected_date_str = selected_date.strftime("%d %B %Y")
        some_redis[callback_query.message.chat.username] = {}
        some_redis[callback_query.message.chat.username]["on_date"] = selected_date_str
        if selected_date.date() < datetime.now().date():
            await callback_query.message.answer(
                f"⛔ Вы выбрали {selected_date_str}\nНельзя выбрать прошедшую дату, повторите выбор",
                reply_markup=await SimpleCalendar().start_calendar(),
            )
        elif selected_date.date() in days_off:
            await callback_query.message.answer(
                f"⛔ Вы выбрали {selected_date.strftime('%d %B %Y')}\nК сожалению это выходной, повторите выбор",
                reply_markup=await SimpleCalendar().start_calendar(),
            )
        elif selected_date.date() in unavailable_days:
            await callback_query.message.answer(
                f"⛔ Вы выбрали {selected_date.strftime('%d %B %Y')}\nК сожалению на этот день запись уже закрыта, повторите выбор",
                reply_markup=await SimpleCalendar().start_calendar(),
            )
        elif selected_date.date() not in available_days:
            await callback_query.message.answer(
                f"⛔ Вы выбрали {selected_date.strftime('%d %B %Y')}\nК сожалению запись на далекое будущее не делаем, повторите выбор",
                reply_markup=await SimpleCalendar().start_calendar(),
            )
        else:
            buttons = []
            slots = await find_free_slots(selected_date.date())
            if len(slots) > 4:
                buttons.append(
                    [
                        InlineKeyboardButton(
                            text=f"{index}", callback_data=f"time_{index}"
                        )
                        for index in slots[:4]
                    ]
                )
                buttons.append(
                    [
                        InlineKeyboardButton(
                            text=f"{index}", callback_data=f"time_{index}"
                        )
                        for index in slots[4:]
                    ]
                )
            else:
                buttons.append(
                    [
                        InlineKeyboardButton(
                            text=f"{index}", callback_data=f"time_{index}"
                        )
                        for index in slots
                    ]
                )
            keyboard = InlineKeyboardMarkup(inline_keyboard=buttons, hide=True)
            await callback_query.message.edit_text(
                "🕛 Выберите свободное время",
                reply_markup=keyboard,
                resize_keyboard=True,
            )


@dp.callback_query(lambda query: query.data.startswith("time_"))
async def get_time(callback_query: CallbackQuery):
    selected_time_str = callback_query.data.split("_")[1]
    some_redis[callback_query.message.chat.username]["on_time"] = selected_time_str
    buttons = [
        [
            InlineKeyboardButton(text=f"{index}", callback_data=f"conf_{index}")
            for index in ["✅ Подтвердить", "❌ Отменить"]
        ]
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons, hide=True)
    await callback_query.message.edit_text(
        f"👍 Отлично, подтвердите запись на\n 🗓 Дата:"
        f" {some_redis[callback_query.message.chat.username]['on_date']}\n ⌚ Время: {some_redis[callback_query.message.chat.username]['on_time']}",
        reply_markup=keyboard,
        resize_keyboard=True,
    )


@dp.callback_query(lambda query: query.data.startswith("conf_"))
async def get_confirm(callback_query: CallbackQuery):
    confirm = callback_query.data.split("_")[1]
    if confirm.lower() == "✅ подтвердить":
        new_user = BarUser(
            user_id=callback_query.message.chat.id,
            username=callback_query.message.chat.username,
            name=callback_query.message.chat.first_name,
            phone="",
            is_active=True,
        )
        time_slot_id = await get_time_slot_id(
            some_redis[callback_query.message.chat.username]["on_time"]
        )
        bar_user_id = await create_or_get_bar_user(new_user)
        new_appointment = Appointment(
            date=datetime.strptime(
                some_redis[callback_query.message.chat.username]["on_date"], "%d %B %Y"
            ).date(),
            time_slot_id=time_slot_id,
            bar_user_id=bar_user_id,
        )
        await create_appointment(new_appointment)

        await callback_query.message.edit_text(
            f"🎉 Отлично, Вы записаны на\nДату: {some_redis[callback_query.message.chat.username]['on_date']}\n"
            f"Время: {some_redis[callback_query.message.chat.username]['on_time']}!\n"
            f"В день стрижки 🤖 - Бот отправит напоминание\n\n",
            resize_keyboard=True,
        )
        user_phone_number = await get_bar_user_phone_number(bar_user_id)
        if not user_phone_number:
            markup = ReplyKeyboardMarkup(
                resize_keyboard=True,
                keyboard=[
                    [
                        KeyboardButton(
                            text="📱 Отправить номер телефона", request_contact=True
                        )
                    ]
                ],
                one_time_keyboard=True,
            )
            await callback_query.message.answer(
                "Отправьте номер телефона для возможности с Вами связаться",
                resize_keyboard=True,
                reply_markup=markup,
            )
    else:
        await callback_query.message.edit_text(
            "Вы отменили запись!",
        )

    del some_redis[callback_query.message.chat.username]


@dp.message(F.contact)
async def func_contact(message: Message):
    updated_user_params = {"phone": message.contact.phone_number}
    await update_bar_user(message.chat.id, **updated_user_params)
    await message.answer(
        "Спасибо, Ваш номер сохранен!",
        resize_keyboard=True,
        reply_markup=ReplyKeyboardRemove(),
    )
    await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)


async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

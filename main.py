import asyncio
import json
import logging

from aiogram import Dispatcher
from aiogram.filters import Command
from aiogram.types import Message

from config import bot
from db.db_session import redis
from handlers.admin.edit_appointments import admin_edit
from handlers.admin.edit_users import admin_edit_users
from handlers.admin.get_appointments import admin_get
from handlers.client import client_router
from keyboards.admin import get_admin_choice_buttons

# Bot
dp = Dispatcher()
dp.include_routers(admin_get, admin_edit, admin_edit_users, client_router)

# Configure logging
logging.basicConfig(level=logging.INFO)


@dp.message(Command("admin"))
async def command_admin(message: Message) -> None:
    keyboard = await get_admin_choice_buttons()
    await message.answer(
        "🕹 Панель администратора\n",
        reply_markup=keyboard,
        resize_keyboard=True,
    )


async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)
    await redis.set("unavailable_days", json.dumps([]))
    await redis.set("admin_date_off", json.dumps([]))
    await redis.set("available_days", json.dumps([]))
    await redis.set("date_off", json.dumps([]))

if __name__ == "__main__":
    asyncio.run(main())

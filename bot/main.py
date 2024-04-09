import asyncio
import logging

from aiogram import Dispatcher
from aiogram.filters import Command
from aiogram.types import Message

from bot.config import bot
from bot.handlers.admin.edit_appointments import admin_edit
from bot.handlers.admin.edit_days import admin_edit_days
from bot.handlers.admin.edit_users import admin_edit_users
from bot.handlers.admin.get_appointments import admin_get
from bot.handlers.client import client_router
from bot.keyboards.admin import get_admin_choice_buttons

# Bot
dp = Dispatcher()
dp.include_routers(admin_get, admin_edit, admin_edit_users, admin_edit_days, client_router)

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


if __name__ == "__main__":
    asyncio.run(main())

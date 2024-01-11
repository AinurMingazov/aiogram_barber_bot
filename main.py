import asyncio
import logging

from aiogram import Dispatcher

from config import bot
from handlers.admin import admin_router
from handlers.client import client_router

# Bot
dp = Dispatcher()
dp.include_routers(admin_router, client_router)

# Configure logging
logging.basicConfig(level=logging.INFO)


async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

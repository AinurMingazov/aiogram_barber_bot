import os

from aiogram import Bot

some_redis = {"unavailable_days": [], "admin_date_off": [], "available_days": [], "date_off": []}

bot = Bot(token=os.getenv("BBOT_TOKEN", ""), parse_mode="HTML")

admin_id = os.getenv("ADMIN_ID", "")

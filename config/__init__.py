import os

from aiogram import Bot

some_redis = {}

bot = Bot(token=os.getenv("BBOT_TOKEN", ""), parse_mode="HTML")

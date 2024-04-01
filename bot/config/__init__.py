import os
from datetime import datetime

from aiogram import Bot

common_dates = {"unavailable_days": [], "admin_date_off": [], "available_days": [], "date_off": []}

bot = Bot(token=os.getenv("BBOT_TOKEN", ""), parse_mode="HTML")

admin_id = int(os.getenv("ADMIN_ID", ""))

calendar_dates_range = datetime(2022, 1, 1), datetime(2025, 12, 31)

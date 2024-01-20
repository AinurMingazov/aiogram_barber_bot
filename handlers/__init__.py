from aiogram.filters.callback_data import CallbackData
from datetime import time


class AdminCallback(CallbackData, prefix="admin"):
    action: str

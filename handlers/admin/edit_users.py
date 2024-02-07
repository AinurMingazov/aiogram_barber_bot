from aiogram import F, Router
from aiogram.types import CallbackQuery

from handlers import AdminCallback
from keyboards.admin import get_admin_clients_buttons

admin_edit_users = Router()


@admin_edit_users.callback_query(AdminCallback.filter(F.action == "edit_users"))
async def edit_users(callback_query: CallbackQuery, callback_data: AdminCallback):
    keyboard = await get_admin_clients_buttons()

    await callback_query.message.edit_text(f"Клиенты", reply_markup=keyboard, resize_keyboard=True)

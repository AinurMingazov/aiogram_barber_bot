from aiogram import F, Router
from aiogram.types import CallbackQuery
from aiogram.utils.markdown import hbold

from handlers import AdminCallback
from services.users import get_users_name_phone

admin_edit_users = Router()


@admin_edit_users.callback_query(AdminCallback.filter(F.action == "edit_users"))
async def edit_users(callback_query: CallbackQuery, callback_data: AdminCallback):
    users_name_phone = await get_users_name_phone()

    answer = ""
    for user in users_name_phone:
        answer += f"🧒 {hbold(user[0])} 📞 {user[1]}\n"
    await callback_query.message.edit_text(answer)

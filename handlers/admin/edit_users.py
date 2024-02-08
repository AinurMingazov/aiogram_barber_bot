from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from config import some_redis
from handlers import AdminCallback
from keyboards.admin import get_admin_clients_buttons, get_admin_clients_edit_buttons
from services.users import update_bar_user_by_id

admin_edit_users = Router()


class ClientEditForm(StatesGroup):
    edit_field = State()


@admin_edit_users.callback_query(AdminCallback.filter(F.action == "edit_users"))
async def choose_user(callback_query: CallbackQuery, callback_data: AdminCallback):
    keyboard = await get_admin_clients_buttons()
    await callback_query.message.edit_text("Клиенты", reply_markup=keyboard, resize_keyboard=True)


@admin_edit_users.callback_query(AdminCallback.filter(F.action.startswith("id_")))
async def choose_change_param(callback_query: CallbackQuery):
    user_id = callback_query.data.split("_")[1]
    some_redis[callback_query.message.chat.id] = {}
    some_redis[callback_query.message.chat.id]["user_id"] = user_id
    keyboard = await get_admin_clients_edit_buttons()
    await callback_query.message.edit_text("Редактировать", reply_markup=keyboard, resize_keyboard=True)


@admin_edit_users.callback_query(AdminCallback.filter(F.action.startswith("edit_")))
async def process_change_param(callback_query: CallbackQuery, state: FSMContext, callback_data: AdminCallback):
    edit_choice = callback_query.data.split("_")[1]
    if edit_choice == "name":
        await state.set_state(ClientEditForm.edit_field)
        some_redis[callback_query.message.chat.id]["choice"] = "name"
        await callback_query.message.edit_text("Напиши имя клиента")
    if edit_choice == "phone":
        await state.set_state(ClientEditForm.edit_field)
        some_redis[callback_query.message.chat.id]["choice"] = "phone"
        await callback_query.message.edit_text("Напиши номер телефона клиента (Пример: 89123456789)")


@admin_edit_users.message(ClientEditForm.edit_field)
async def save_changes(message: Message, state: FSMContext) -> None:
    data = some_redis[message.chat.id]
    updated_user_params = {data["choice"]: message.text}
    await update_bar_user_by_id(data["user_id"], **updated_user_params)
    if data["choice"] == "name":
        await message.answer(f"👍 Имя клиента изменено на {message.text}")
    elif data["choice"] == "phone":
        await message.answer(f"👍 Номер клиента изменен на {message.text}")

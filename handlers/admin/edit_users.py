from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from config import some_redis
from handlers import AdminCallback
from keyboards.admin import get_admin_clients_buttons, get_admin_clients_edit_buttons, get_admin_confirm_change_user
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
    bar_user_id = callback_query.data.split("_")[1]
    some_redis[callback_query.message.chat.id] = {}
    some_redis[callback_query.message.chat.id]["bar_user_id"] = bar_user_id
    keyboard = await get_admin_clients_edit_buttons()
    await callback_query.message.edit_text("Редактировать", reply_markup=keyboard, resize_keyboard=True)


@admin_edit_users.callback_query(AdminCallback.filter(F.action.startswith("edit_")))
async def process_change_param(callback_query: CallbackQuery, state: FSMContext, callback_data: AdminCallback):
    edit_choice = callback_query.data.split("_")[1]
    if edit_choice == "name":
        await state.set_state(ClientEditForm.edit_field)
        some_redis[callback_query.message.chat.id]["choice"] = "name"
        await callback_query.message.edit_text("Напиши имя клиента")
    elif edit_choice == "phone":
        await state.set_state(ClientEditForm.edit_field)
        some_redis[callback_query.message.chat.id]["choice"] = "phone"
        await callback_query.message.edit_text("Напиши номер телефона клиента (Пример: 89123456789)")


@admin_edit_users.message(ClientEditForm.edit_field)
async def save_changes(message: Message, state: FSMContext) -> None:
    data = some_redis[message.chat.id]
    keyboard = await get_admin_confirm_change_user(message.text)
    if data["choice"] == "name":
        await message.answer(
            f"👍 Изменить имя клиента на {message.text}",
            reply_markup=keyboard,
            resize_keyboard=True,
        )
    elif data["choice"] == "phone":
        await message.answer(
            f"👍 Изменить номер клиента на {message.text}",
            reply_markup=keyboard,
            resize_keyboard=True,
        )
    await state.update_data(name=message.text)
    await state.clear()


@admin_edit_users.callback_query(AdminCallback.filter(F.action.startswith("confuser_")))
async def get_confirm(callback_query: CallbackQuery):
    response = callback_query.data.split("_")
    confirm, value = response[1], response[2]
    if int(confirm):
        data = some_redis[callback_query.message.chat.id]
        updated_user_params = {data["choice"]: value}
        await update_bar_user_by_id(int(data["bar_user_id"]), **updated_user_params)
        await callback_query.message.edit_text(
            "🎉 Данные клиента изменены",
            resize_keyboard=True,
        )
    else:
        await callback_query.message.edit_text("Вы отменили изменения!")
    del some_redis[callback_query.message.chat.id]

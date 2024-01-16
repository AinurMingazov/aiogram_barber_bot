from datetime import datetime
from aiogram.types import Message


from config import some_redis
from models import Appointment, BarUser
from services.database_queries import (create_appointment,
                                       create_or_get_bar_user,
                                       get_time_slot_id,)


async def add_appointment(message: Message) -> int:
    new_user = BarUser(
        user_id=message.chat.id,
        username=message.chat.username if message.chat.username else None,
        name=message.chat.first_name if message.chat.first_name else None,
        is_active=True,
    )
    time_slot_id = await get_time_slot_id(some_redis[message.chat.id]["on_time"])
    bar_user_id = await create_or_get_bar_user(new_user)
    new_appointment = Appointment(
        date=datetime.strptime(
            some_redis[message.chat.id]["on_date"], "%d %B %Y"
        ).date(),
        time_slot_id=time_slot_id,
        bar_user_id=bar_user_id,
    )
    await create_appointment(new_appointment)
    return bar_user_id

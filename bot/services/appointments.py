import json
from datetime import datetime

from aiogram.types import Message
from sqlalchemy import delete, text, update

from api.models import BarUser, Appointment
from bot.services.time_slots import get_time_slot_id
from bot.services.users import create_or_get_bar_user
from db.db_session import redis, async_session


async def add_appointment(message: Message) -> tuple[int, int]:
    new_user = BarUser(
        user_id=message.chat.id,
        username=message.chat.username if message.chat.username else None,
        name=message.chat.first_name if message.chat.first_name else None,
        is_active=True,
    )
    appointment_cache = json.loads(await redis.get(message.chat.id))
    time_slot_id = await get_time_slot_id(appointment_cache["on_time"])
    bar_user_id = await create_or_get_bar_user(new_user)
    new_appointment = Appointment(
        date=datetime.strptime(appointment_cache["on_date"], "%d %B %Y").date(),
        time_slot_id=time_slot_id,
        bar_user_id=bar_user_id,
        is_approved=False,
    )
    appointment_id = await create_appointment(new_appointment)
    return bar_user_id, appointment_id


async def add_admin_appointment(message: Message) -> int:
    appointment_cache = json.loads(await redis.get(message.chat.id))
    new_user = BarUser(
        user_id=None,
        username=None,
        name=appointment_cache["user_name"],
        is_active=True,
    )
    time_slot_id = await get_time_slot_id(appointment_cache["on_time"])
    bar_user_id = await create_bar_user(new_user)
    new_appointment = Appointment(
        date=datetime.strptime(appointment_cache["on_date"], "%d %B %Y").date(),
        time_slot_id=time_slot_id,
        bar_user_id=bar_user_id,
        is_approved=True,
    )
    await create_appointment(new_appointment)
    return bar_user_id


async def create_appointment(new_appointment):
    async with async_session() as session:
        async with session.begin():
            session.add(new_appointment)
            await session.commit()
            return new_appointment.id


async def get_active_appointments(day=None):
    for_day = ""
    if day:
        for_day = f"AND pa.date = '{day}'"
    today = datetime.now().date()
    async with async_session() as session:
        async with session.begin():
            query_appointments = f"""SELECT pa.date, pb.name, pb.phone, pt.time FROM panel_appointment pa
                                       JOIN panel_baruser pb ON  pa.bar_user_id = pb.id
                                       JOIN panel_timeslot pt ON pa.time_slot_id = pt.id
                                      WHERE pa.date >= '{today}'
                                      {for_day}                                  
                                   ORDER BY pa.date, pt.time
            """
            appointments_db = await session.execute(text(query_appointments))
    appointments = appointments_db.all()
    active_appointments_by_dates = {}
    for appointment in appointments:
        if appointment.date in active_appointments_by_dates:
            active_appointments_by_dates[appointment.date].append(
                {
                    "user_name": appointment.name,
                    "slot_time": appointment.time,
                    "phone": appointment.phone,
                }
            )
        else:
            active_appointments_by_dates[appointment.date] = [
                {
                    "user_name": appointment.name,
                    "slot_time": appointment.time,
                    "phone": appointment.phone,
                }
            ]
    return active_appointments_by_dates


async def get_appointment(appointment_id: int):
    async with async_session() as session:
        async with session.begin():
            query_appointment = f"""
                SELECT pa.date, pb.name, pt.time FROM panel_appointment pa
                 JOIN panel_baruser pb ON  pa.bar_user_id = pb.id
                 JOIN panel_timeslot pt ON pa.time_slot_id = pt.id
                WHERE pa.id = {appointment_id}
            """
            appointment_db = await session.execute(text(query_appointment))
        appointment = appointment_db.first()
        return appointment


async def update_appointment(appointment_id, **kwargs):
    async with async_session() as session:
        async with session.begin():
            query_appointment = update(Appointment).where(Appointment.id == appointment_id).values(kwargs)
            await session.execute(query_appointment)


async def del_appointment(appointment_id):
    async with async_session() as session:
        async with session.begin():
            query_appointment = delete(Appointment).where(Appointment.id == appointment_id)
            await session.execute(query_appointment)

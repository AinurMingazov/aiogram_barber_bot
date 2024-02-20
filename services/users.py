from datetime import datetime

from sqlalchemy import and_, select, update

from models import Appointment, BarUser, TimeSlot
from session import async_session


async def get_active_users():
    conn = async_session()
    async with conn.begin():
        query_users = select(BarUser).filter(BarUser.is_active.is_(True))
        tmp_users = await conn.execute(query_users)
        users = [[user.id, user.phone, user.name] for user in tmp_users.scalars().all()]
        return users


async def create_or_get_bar_user(new_user):
    conn = async_session()
    async with conn.begin():
        query_bar_user = select(BarUser).filter(BarUser.user_id == new_user.user_id)
        existing_user = await conn.execute(query_bar_user)
        existing_user = existing_user.scalars().first()
        if existing_user:
            return existing_user.id

        conn.add(new_user)
        await conn.commit()
        return new_user.id


async def create_bar_user(new_user):
    conn = async_session()
    async with conn.begin():
        conn.add(new_user)
        await conn.commit()
        return new_user.id


async def get_bar_user_phone_number(bar_user_id):
    conn = async_session()
    async with conn.begin():
        query_bar_user = select(BarUser).filter(BarUser.id == bar_user_id)
        bar_user_db = await conn.execute(query_bar_user)
        bar_user = bar_user_db.scalars().first()
        if bar_user:
            return bar_user.phone


async def update_bar_user(user_id, **kwargs):
    conn = async_session()
    async with conn.begin():
        query_bar_user = update(BarUser).filter(BarUser.user_id == user_id).values(kwargs)
        await conn.execute(query_bar_user)


async def get_user_have_active_appointment(user_id):
    conn = async_session()
    async with conn.begin():
        bar_user_query = select(BarUser).filter(BarUser.user_id == user_id)
        bar_user_db = await conn.execute(bar_user_query)
    bar_user = bar_user_db.scalars().first()
    if not bar_user:
        return bar_user

    today = datetime.now().date()
    conn = async_session()
    async with conn.begin():
        active_appointment_query = select(Appointment).filter(
            and_(Appointment.bar_user_id == bar_user.id, Appointment.date >= today)
        )
        active_appointment_db = await conn.execute(active_appointment_query)
    active_appointment = active_appointment_db.scalars().first()

    if not active_appointment:
        return active_appointment
    else:
        conn = async_session()
        async with conn.begin():
            slot_query = select(TimeSlot).filter(TimeSlot.id == active_appointment.time_slot_id)
            slot_db = await conn.execute(slot_query)
        slot = slot_db.scalars().first()
        return active_appointment.date, slot.time

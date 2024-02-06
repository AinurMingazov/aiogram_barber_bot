from datetime import time

from sqlalchemy import select, text

from models import TimeSlot
from session import async_session


async def get_time_slot_id(time_str):
    time_slot = time(*map(int, time_str.split(":")))
    conn = async_session()
    async with conn.begin():
        slot_query = select(TimeSlot).filter(TimeSlot.time == time_slot)
        slot_db = await conn.execute(slot_query)
    slot = slot_db.scalars().first()
    return slot.id


async def find_slots():
    conn = async_session()
    async with conn.begin():
        slots_query = select(TimeSlot)
        slots_db = await conn.execute(slots_query)
    slots = slots_db.scalars().all()
    slot_time = [slot for slot in slots]
    return slot_time


async def find_free_slots(day):
    day.strftime("%Y-%m-%d")

    conn = async_session()
    async with conn.begin():
        query_appointment = f"""SELECT pa.time_slot_id FROM panel_appointment pa
                                WHERE pa.date = '{day.strftime('%Y-%m-%d')}'
        """
        busy_slots_db = await conn.execute(text(query_appointment))
        slots_query = select(TimeSlot)
        slots_db = await conn.execute(slots_query)
    busy_slots = busy_slots_db.scalars().all()
    busy_slot_ids = [slot_id for slot_id in busy_slots]
    slots = slots_db.scalars().all()
    slot_time = [slot for slot in slots if slot.id not in busy_slot_ids]
    return slot_time

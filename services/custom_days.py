from datetime import datetime, timedelta
from sqlalchemy import text, select, func, cast, Date, and_

from models import TimeSlot, Appointment, CustomDay
from session import async_session


async def get_unavailable_days():
    full_work_days = ['2024-02-23', '2024-02-24', '2024-02-25']
    half_work_days = ['2024-02-23', '2024-02-24', '2024-02-25']
    unavailable_full_work_days = await get_unavailable_work_days(full_work_days, 'FULL_WORK')
    unavailable_half_work_days = await get_unavailable_work_days(half_work_days, 'HALF_WORK')
    return unavailable_full_work_days + unavailable_half_work_days


async def get_unavailable_work_days(days, day_type=None):
    n = 1
    if day_type == 'HALF_WORK':
        n = 2
    today = datetime.now().date()
    conn = async_session()
    async with conn.begin():

        subquery = select(func.count(TimeSlot.id)/n).scalar_subquery()
        unavailable_work_days_query = select(Appointment.date).filter(
            Appointment.date.in_([
                today,
                ])).join(TimeSlot).group_by(Appointment.date).having(func.count(TimeSlot.id.distinct()) == subquery)
        unavailable_work_days_db = await conn.execute(unavailable_work_days_query)

    unavailable_work_days = unavailable_work_days_db.scalars().all()
    unavailable_work_days = [day for day in unavailable_work_days]

    return unavailable_work_days


async def get_custom_days(day_type: str = 'DAY_OFF'):
    today = datetime.now().date()
    conn = async_session()
    async with conn.begin():
        query_days = select(CustomDay.date).filter(
            and_(CustomDay.date >= today, CustomDay.day_type == day_type)
        )
        days_db = await conn.execute(query_days)
        days = days_db.scalars().all()
    return days


async def create_custom_day(new_custom_day):
    conn = async_session()
    async with conn.begin():
        conn.add(new_custom_day)
        await conn.commit()
        return new_custom_day.date


async def get_active_admin_days():
    today = datetime.now().date()
    conn = async_session()
    async with conn.begin():
        query_days = select(CustomDay.date).filter(CustomDay.date >= today)
        days_db = await conn.execute(query_days)
        days = days_db.scalars().all()
    return days


async def get_admin_day_status(day):
    conn = async_session()
    async with conn.begin():
        query_day_type = select(CustomDay.day_type).filter(CustomDay.date == day)
        day_type_db = await conn.execute(query_day_type)
        day_type = day_type_db.scalars().first()
    return day_type

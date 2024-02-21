from datetime import datetime, timedelta
from sqlalchemy import text, select, func, cast, Date

from models import TimeSlot, Appointment
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


async def get_admin_date_off():
    today = datetime.now().date()
    conn = async_session()
    async with conn.begin():
        query_day_off = f"""SELECT date 
                              FROM panel_customday 
                             WHERE date >= '{today}'
                               AND day_type = 'DAY_OFF'
        """
        day_off_db = await conn.execute(text(query_day_off))
    days_off = [day.date for day in day_off_db.all()]
    return days_off


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
        query_day = f"""SELECT date FROM panel_customday WHERE date >= '{today}'"""
        day_db = await conn.execute(text(query_day))
    admin_days = [day.date for day in day_db.all()]
    return admin_days


async def get_admin_day_status(day):
    conn = async_session()
    async with conn.begin():
        query_day = f"""SELECT day_type FROM panel_customday WHERE date = '{day}'"""
        day_db = await conn.execute(text(query_day))
    day_type = day_db.scalars().first()
    return day_type

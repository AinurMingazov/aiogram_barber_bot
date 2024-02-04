from datetime import datetime, timedelta

from sqlalchemy import text

from session import async_session


async def get_unavailable_days():
    conn = async_session()
    async with conn.begin():
        today = datetime.now().date()
        start_date = today + timedelta(days=1)
        end_date = today + timedelta(days=21)
        start_date = start_date.strftime("%Y-%m-%d")
        end_date = end_date.strftime("%Y-%m-%d")

        query_appointment = f"""select pa.date, count(*) from panel_appointment pa
                                where pa.date between '{start_date}' and '{end_date}'
                                group by pa.date
                                having count(*) >= 8
        """
        unavailable_days = await conn.execute(text(query_appointment))
        unavailable_dates = [day.date for day in unavailable_days]
        return unavailable_dates


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

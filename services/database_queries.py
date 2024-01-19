from datetime import date, datetime, time, timedelta

from sqlalchemy import and_, select, text, update
from workalendar.europe import Russia

from models import Appointment, BarUser, TimeSlot
from session import async_session


def get_dates(showed_days: int = 28) -> list[date]:
    today = datetime.now().date()
    first_day = datetime.fromisocalendar(today.year, today.isocalendar()[1], 1).date()
    dates = [first_day + timedelta(days=i) for i in range(showed_days)]
    return dates


def get_days_off() -> list[date]:
    dates = get_dates()
    days_off = []
    # Get sundays
    sundays = [day for day in dates if day.weekday() == 6]
    days_off.extend(sundays)

    # Get russian holidays
    cal = Russia()
    holidays = cal.holidays(dates[0].year) + cal.holidays(dates[0].year + 1)
    holidays = [day[0] for day in holidays]
    days_off.extend(holidays)

    return days_off


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


def get_available_days():
    today = datetime.now().date()
    start_date = today + timedelta(days=1)
    end_date = today + timedelta(days=21)
    available_dates = [
        start_date + timedelta(days=x) for x in range((end_date - start_date).days + 1)
    ]
    return available_dates


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


async def find_slots():
    conn = async_session()
    async with conn.begin():
        slots_query = select(TimeSlot)
        slots_db = await conn.execute(slots_query)
    slots = slots_db.scalars().all()
    slot_time = [slot for slot in slots]
    return slot_time


async def get_time_slot_id(time_str):
    time_slot = time(*map(int, time_str.split(":")))
    conn = async_session()
    async with conn.begin():
        slot_query = select(TimeSlot).filter(TimeSlot.time == time_slot)
        slot_db = await conn.execute(slot_query)
    slot = slot_db.scalars().first()
    return slot.id


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
        query_bar_user = (
            update(BarUser).where(and_(BarUser.user_id == user_id)).values(kwargs)
        )
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
            slot_query = select(TimeSlot).filter(
                TimeSlot.id == active_appointment.time_slot_id
            )
            slot_db = await conn.execute(slot_query)
        slot = slot_db.scalars().first()
        return active_appointment.date, slot.time


async def create_appointment(new_appointment):
    conn = async_session()
    async with conn.begin():
        conn.add(new_appointment)
        await conn.commit()
        return new_appointment.id


async def get_active_appointments():
    today = datetime.now().date()
    conn = async_session()
    async with conn.begin():
        query_appointments = f"""SELECT pa.date, pb.name, pb.phone, pt.time FROM panel_appointment pa
                                   JOIN panel_baruser pb ON  pa.bar_user_id = pb.id
                                   JOIN panel_timeslot pt ON pa.time_slot_id = pt.id
                                  WHERE pa.date >= '{today}'                                  
                               ORDER BY pa.date, pt.time
        """
        appointments_db = await conn.execute(text(query_appointments))
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


async def get_admin_date_off():
    today = datetime.now().date()
    conn = async_session()
    async with conn.begin():
        query_day_off = f"""SELECT date FROM panel_dayoff WHERE date >= '{today}'"""
        day_off_db = await conn.execute(text(query_day_off))
    days_off = [day.date for day in day_off_db.all()]
    return days_off

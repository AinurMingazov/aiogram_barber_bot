from datetime import datetime

from sqlalchemy import and_, func, select

from db.db_session import async_session
from models import Appointment, CustomDay, TimeSlot
from services.calendar_days import get_days_off, get_full_work_days, get_half_work_days


async def get_unavailable_days():
    half_work_days = get_half_work_days() + await get_custom_days("HALF_WORK")
    unavailable_half_work_days = await get_unavailable_work_days(half_work_days, "HALF_WORK")

    full_work_days = get_full_work_days() + await get_custom_days("FULL_WORK")
    unavailable_full_work_days = await get_unavailable_work_days(full_work_days, "FULL_WORK")

    return unavailable_full_work_days + unavailable_half_work_days


async def get_unavailable_work_days(days, day_type=None):
    n = 1
    if day_type == "HALF_WORK":
        n = 2
    async with async_session() as session:
        async with session.begin():
            subquery = select(func.count(TimeSlot.id) / n).scalar_subquery()
            unavailable_work_days_query = (
                select(Appointment.date)
                .filter(Appointment.date.in_(days))
                .join(TimeSlot)
                .group_by(Appointment.date)
                .having(func.count(TimeSlot.id.distinct()) == subquery)
            )
            unavailable_work_days_db = await session.execute(unavailable_work_days_query)

            unavailable_work_days = unavailable_work_days_db.scalars().all()
            unavailable_work_days = [day for day in unavailable_work_days]

            return unavailable_work_days


async def get_custom_days(day_type: str = "DAY_OFF"):
    today = datetime.now().date()
    async with async_session() as session:
        async with session.begin():
            query_days = select(CustomDay.date).filter(and_(CustomDay.date >= today, CustomDay.day_type == day_type))
            days_db = await session.execute(query_days)
            days = days_db.scalars().all()
            return days


async def create_custom_day(new_custom_day):
    async with async_session() as session:
        async with session.begin():
            session.add(new_custom_day)
            await session.commit()
            return new_custom_day.date


async def get_active_admin_days():
    today = datetime.now().date()
    async with async_session() as session:
        async with session.begin():
            query_days = select(CustomDay.date).filter(CustomDay.date >= today)
            days_db = await session.execute(query_days)
            days = days_db.scalars().all()
            return days


async def get_admin_day_status(day):
    async with async_session() as session:
        async with session.begin():
            query_day_type = select(CustomDay.day_type).filter(CustomDay.date == day)
            day_type_db = await session.execute(query_day_type)
            day_type = day_type_db.scalars().first()
            return day_type


async def get_day_status(day):
    admin_days = await get_active_admin_days()
    if day not in admin_days:
        days_off = get_days_off()
        half_work = get_half_work_days()
        if day in days_off:
            return "dayoff"
        elif day in half_work:
            return "halfwork"
        else:
            return "fullwork"
    else:
        day_type = await get_admin_day_status(day)
        return day_type

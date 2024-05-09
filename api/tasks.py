import os
from datetime import datetime, timedelta

import httpx
from sqlalchemy import and_, select
from sqlalchemy.orm import joinedload

from api.models import Appointment
from db.db_session import async_session


async def send_one_hour_behind_appointment():
    db = async_session()
    current_time = datetime.now().time()
    one_hour_later = (datetime.now() + timedelta(hours=1)).time()

    try:
        db = async_session()
        query_appointment = (
            select(Appointment)
            .options(joinedload(Appointment.bar_user), joinedload(Appointment.time_slot))
            .filter(
                and_(
                    Appointment.is_approved.is_(True),
                    Appointment.date == datetime.now().date(),
                )
            )
        )
        query = await db.execute(query_appointment)
        appointments = query.scalars().all()
        users = [
            appointment.bar_user
            for appointment in appointments
            if appointment.time_slot.time > current_time and appointment.time_slot.time < one_hour_later
        ]
        if users:
            user = users[0]
        else:
            return

        base_url = f'https://api.telegram.org/bot{os.getenv("BBOT_TOKEN", "")}/sendMessage'

        params = {"chat_id": user.user_id, "text": f"Привет, {user.name}! ждем Вас на стрижку через час!"}

        async with httpx.AsyncClient() as client:
            response = await client.post(base_url, json=params)
        print(response.status_code)
    except Exception as e:
        print(e)
    finally:
        await db.close()


async def send_two_weeks_after_appointment():
    db = async_session()
    two_weeks_before = (datetime.now() - timedelta(days=14)).date()

    try:
        db = async_session()
        query_appointment = (
            select(Appointment)
            .options(joinedload(Appointment.bar_user), joinedload(Appointment.time_slot))
            .filter(
                and_(
                    Appointment.is_approved.is_(True),
                    Appointment.date == two_weeks_before,
                )
            )
        )
        query = await db.execute(query_appointment)
        appointments = query.scalars().all()
        users = [appointment.bar_user for appointment in appointments]
        if users:
            for user in users:
                base_url = f'https://api.telegram.org/bot{os.getenv("BBOT_TOKEN", "")}/sendMessage'

                params = {
                    "chat_id": user.user_id,
                    "text": f"Привет, {user.name}!"
                    f" Напоминаю Вы стриглись 2 недели назад, возможно стоит снова записаться",
                }

                async with httpx.AsyncClient() as client:
                    response = await client.post(base_url, json=params)
                print(response.status_code)
        else:
            return

    except Exception as e:
        print(e)
    finally:
        await db.close()

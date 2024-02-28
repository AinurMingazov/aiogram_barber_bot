from config import some_redis
from services.calendar_days import get_available_days, get_days_off
from services.custom_days import get_custom_days, get_unavailable_days


async def update_redis_cache():
    unavailable_days = await get_unavailable_days()
    some_redis["unavailable_days"] = unavailable_days

    admin_date_off = await get_custom_days()
    some_redis["admin_date_off"] = admin_date_off

    available_days = get_available_days()
    some_redis["available_days"] = available_days

    date_off = get_days_off()
    some_redis["date_off"] = date_off

from config import some_redis
from services.database_queries import get_admin_date_off, get_available_days, get_days_off, get_unavailable_days


async def update_redis_cache():
    unavailable_days = await get_unavailable_days()
    some_redis["unavailable_days"] = unavailable_days

    admin_date_off = await get_admin_date_off()
    some_redis["admin_date_off"] = admin_date_off

    available_days = get_available_days()
    some_redis["available_days"] = available_days

    date_off = get_days_off()
    some_redis["date_off"] = date_off

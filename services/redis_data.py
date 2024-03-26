from config import common_dates
from services.calendar_days import get_available_days, get_days_off
from services.custom_days import get_custom_days, get_unavailable_days


async def update_common_dates():
    unavailable_days = await get_unavailable_days()
    common_dates["unavailable_days"] = unavailable_days

    admin_date_off = await get_custom_days()
    common_dates["admin_date_off"] = admin_date_off

    available_days = get_available_days()
    common_dates["available_days"] = available_days

    date_off = get_days_off()
    common_dates["date_off"] = date_off

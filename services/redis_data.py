from config import common_dates
from services.calendar_days import get_available_days, get_half_work_days, get_days_off
from services.custom_days import get_custom_days, get_unavailable_days


async def update_common_dates():
    unavailable_days = get_days_off()
    common_dates["unavailable_days"] = unavailable_days

    half_work_days = get_half_work_days()
    common_dates["half_work_days"] = half_work_days

    available_days = get_available_days() + await get_custom_days("FULL_WORK")
    common_dates["available_days"] = available_days

    closed_dates = await get_unavailable_days()
    common_dates["closed_dates"] = closed_dates

    custom_unavailable_days = await get_custom_days("DAY_OFF")
    common_dates["custom_unavailable_days"] = custom_unavailable_days

    custom_half_work_days = await get_custom_days("HALF_WORK")
    common_dates["custom_half_work_days"] = custom_half_work_days

    custom_available_days = await get_custom_days("FULL_WORK")
    common_dates["custom_available_days"] = custom_available_days

    all_custom_days = custom_unavailable_days + custom_half_work_days + custom_available_days
    common_dates["all_custom_days"] = all_custom_days

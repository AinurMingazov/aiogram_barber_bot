from services.database_queries import get_active_admin_days, get_admin_day_status, get_days_off, get_half_work_days


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

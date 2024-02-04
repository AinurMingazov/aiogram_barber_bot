from datetime import date, datetime, timedelta

from workalendar.europe import Russia

from services.custom_days import get_active_admin_days, get_admin_day_status


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


def get_dates(showed_days: int = 95) -> list[date]:
    today = datetime.now().date()
    first_day = datetime.fromisocalendar(today.year, today.isocalendar()[1], 1).date()
    dates = [first_day + timedelta(days=i) for i in range(showed_days)]
    return dates


def get_available_days():
    today = datetime.now().date()
    start_date = today + timedelta(days=1)
    end_date = today + timedelta(days=21)
    available_dates = [start_date + timedelta(days=x) for x in range((end_date - start_date).days + 1)]
    return available_dates


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


def get_half_work_days() -> list[date]:
    """Get saturdays"""
    dates = get_dates()
    return [day for day in dates if day.weekday() == 5]

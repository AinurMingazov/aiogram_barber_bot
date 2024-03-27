from datetime import date, datetime, timedelta

from workalendar.europe import Russia


def get_days(showed_days: int = 95) -> list[date]:
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
    days = get_days(21)
    days_off = []
    # Get sundays
    sundays = [day for day in days if day.weekday() == 6]
    days_off.extend(sundays)

    # Get russian holidays
    cal = Russia()
    holidays = cal.holidays(days[0].year) + cal.holidays(days[0].year + 1)
    holidays = [day[0] for day in holidays]
    days_off.extend(holidays)

    return days_off


def get_half_work_days() -> list[date]:
    """Get saturdays"""
    days = get_days(21)
    return [day for day in days if day.weekday() == 5]


def get_full_work_days() -> list[date]:
    """Get saturdays"""
    days = get_days(21)
    return [day for day in days if day.weekday() != 5 or day not in get_days_off()]

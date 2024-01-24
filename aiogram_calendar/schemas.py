from enum import Enum
from typing import Optional

from aiogram.filters.callback_data import CallbackData
from pydantic import BaseModel, Field, conlist


class SimpleCalAct(str, Enum):
    ignore = "IGNORE"
    prev_y = "PREV-YEAR"
    next_y = "NEXT-YEAR"
    prev_m = "PREV-MONTH"
    next_m = "NEXT-MONTH"
    cancel = "CANCEL"
    today = "TODAY"
    day = "DAY"


class DialogCalAct(str, Enum):
    ignore = "IGNORE"
    set_y = "SET-YEAR"
    set_m = "SET-MONTH"
    prev_y = "PREV-YEAR"
    next_y = "NEXT-YEAR"
    cancel = "CANCEL"
    start = "START"
    day = "SET-DAY"


class CalendarCallback(CallbackData, prefix="calendar"):
    act: str
    year: Optional[int] = None
    month: Optional[int] = None
    day: Optional[int] = None
    flag: Optional[str] = 'user'


class SimpleCalendarCallback(CalendarCallback, prefix="simple_calendar"):
    act: SimpleCalAct


class DialogCalendarCallback(CalendarCallback, prefix="dialog_calendar"):
    act: DialogCalAct


class CalendarLabels(BaseModel):
    "Schema to pass labels for calendar. Can be used to put in different languages"

    days_of_week: conlist(str, max_length=7, min_length=7) = [
        "Mo",
        "Tu",
        "We",
        "Th",
        "Fr",
        "Sa",
        "Su",
    ]
    months: conlist(str, max_length=12, min_length=12) = [
        "Jan",
        "Feb",
        "Mar",
        "Apr",
        "May",
        "Jun",
        "Jul",
        "Aug",
        "Sep",
        "Oct",
        "Nov",
        "Dec",
    ]
    cancel_caption: str = Field(
        default="Cancel", description="Caprion for Cancel button"
    )
    today_caption: str = Field(default="Today", description="Caprion for Cancel button")


# HIGHLIGHT_FORMAT = "[{}]"


HIGHLIGHT_FORMAT = "[{}]"
DAYS_OFF = "⁝{}⁝"
UNAVAILABLE_DATES = "∶{}∶"
AVAILABLE_DATES = "∙{}∙"


def highlight(text):
    return HIGHLIGHT_FORMAT.format(text)


def highlight_days_off(text):
    return DAYS_OFF.format(text)


def highlight_unavailable_dates(text):
    return UNAVAILABLE_DATES.format(text)


def highlight_available_dates(text):
    return AVAILABLE_DATES.format(text)


def superscript(text):
    normal = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+-=()"
    super_s = "ᴬᴮᶜᴰᴱᶠᴳᴴᴵᴶᴷᴸᴹᴺᴼᴾQᴿˢᵀᵁⱽᵂˣʸᶻᵃᵇᶜᵈᵉᶠᵍʰᶦʲᵏˡᵐⁿᵒᵖ۹ʳˢᵗᵘᵛʷˣʸᶻ⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻⁼⁽⁾"
    output = ""
    for i in text:
        output += super_s[normal.index(i)] if i in normal else i
    return output

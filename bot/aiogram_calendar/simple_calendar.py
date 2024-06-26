import calendar
import itertools
from datetime import date, datetime, timedelta

from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

from bot.aiogram_calendar.common import GenericCalendar
from bot.aiogram_calendar.schemas import (SimpleCalAct, SimpleCalendarCallback, highlight, highlight_available_dates,
                                          highlight_half_work_dates, highlight_unavailable_dates, superscript)
from bot.services.calendar_days import get_available_days, get_days_off, get_half_work_days
from bot.services.custom_days import get_custom_days, get_unavailable_days


class SimpleCalendar(GenericCalendar):
    ignore_callback = SimpleCalendarCallback(act=SimpleCalAct.ignore).pack()  # placeholder for no answer buttons

    async def start_calendar(
        self, year: int = datetime.now().year, month: int = datetime.now().month, flag: str = "user"
    ) -> InlineKeyboardMarkup:
        """
        Creates an inline keyboard with the provided year and month
        :param flag: Flags with which params show calendar
        :param int year: Year to use in the calendar, if None the current year is used.
        :param int month: Month to use in the calendar, if None the current month is used.
        :return: Returns InlineKeyboardMarkup object with the calendar.
        """
        today = datetime.now()
        now_weekday = self._labels.days_of_week[today.weekday()]
        now_month, now_year, now_day = today.month, today.year, today.day

        unavailable_days = get_days_off()
        half_work_days = get_half_work_days()
        available_days = get_available_days()

        closed_dates = await get_unavailable_days()
        custom_unavailable_days = await get_custom_days("DAY_OFF")
        custom_half_work_days = await get_custom_days("HALF_WORK")
        custom_available_days = await get_custom_days("FULL_WORK")

        def highlight_month():
            month_str = self._labels.months[month - 1]
            if now_month == month and now_year == year:
                return highlight(month_str)
            return month_str

        def highlight_weekday():
            if now_month == month and now_year == year and now_weekday == weekday:
                return highlight(weekday)
            return weekday

        def format_day_string():
            date_to_check = datetime(year, month, day)
            if self.min_date and date_to_check < self.min_date:
                return superscript(str(day))
            elif self.max_date and date_to_check > self.max_date:
                return superscript(str(day))
            return str(day)

        def highlight_day():
            day_string = format_day_string()
            current_date = date(year, month, day)

            if now_month == month and now_year == year and now_day == day:
                return highlight(day_string)
            elif current_date in closed_dates:
                return highlight_unavailable_dates(day_string)
            elif current_date in list(
                itertools.chain(half_work_days + custom_half_work_days)
            ) and current_date not in list(itertools.chain(custom_unavailable_days + custom_available_days)):
                return highlight_half_work_dates(day_string)
            elif current_date in list(
                itertools.chain(unavailable_days + custom_unavailable_days)
            ) and current_date not in list(itertools.chain(custom_half_work_days + custom_available_days)):
                return highlight_unavailable_dates(day_string)
            elif current_date in list(
                itertools.chain(available_days + custom_available_days)
            ) and current_date not in list(itertools.chain(custom_unavailable_days + custom_half_work_days)):
                return highlight_available_dates(day_string)
            return day_string

        # building a calendar keyboard
        kb = []

        # inline_kb = InlineKeyboardMarkup(row_width=7)
        # First row - Year
        years_row = []
        years_row.append(
            InlineKeyboardButton(
                text="<<",
                callback_data=SimpleCalendarCallback(
                    act=SimpleCalAct.prev_y, year=year, month=month, day=1, flag=flag
                ).pack(),
            )
        )
        years_row.append(
            InlineKeyboardButton(
                text=str(year) if year != now_year else highlight(year),
                callback_data=self.ignore_callback,
            )
        )
        years_row.append(
            InlineKeyboardButton(
                text=">>",
                callback_data=SimpleCalendarCallback(
                    act=SimpleCalAct.next_y, year=year, month=month, day=1, flag=flag
                ).pack(),
            )
        )
        kb.append(years_row)

        # Month nav Buttons
        month_row = []
        month_row.append(
            InlineKeyboardButton(
                text="<",
                callback_data=SimpleCalendarCallback(
                    act=SimpleCalAct.prev_m, year=year, month=month, day=1, flag=flag
                ).pack(),
            )
        )
        month_row.append(InlineKeyboardButton(text=highlight_month(), callback_data=self.ignore_callback))
        month_row.append(
            InlineKeyboardButton(
                text=">",
                callback_data=SimpleCalendarCallback(
                    act=SimpleCalAct.next_m, year=year, month=month, day=1, flag=flag
                ).pack(),
            )
        )
        kb.append(month_row)

        # Week Days
        week_days_labels_row = []
        for weekday in self._labels.days_of_week:
            week_days_labels_row.append(
                InlineKeyboardButton(text=highlight_weekday(), callback_data=self.ignore_callback)
            )
        kb.append(week_days_labels_row)

        # Calendar rows - Days of month
        month_calendar = calendar.monthcalendar(year, month)

        for week in month_calendar:
            days_row = []
            for day in week:
                if day == 0:
                    days_row.append(InlineKeyboardButton(text=" ", callback_data=self.ignore_callback))
                    continue
                days_row.append(
                    InlineKeyboardButton(
                        text=highlight_day(),
                        callback_data=SimpleCalendarCallback(
                            act=SimpleCalAct.day, year=year, month=month, day=day, flag=flag
                        ).pack(),
                    )
                )
            kb.append(days_row)

        # nav today & cancel button
        cancel_row = []
        cancel_row.append(
            InlineKeyboardButton(
                text=self._labels.cancel_caption,
                callback_data=SimpleCalendarCallback(
                    act=SimpleCalAct.cancel, year=year, month=month, day=day, flag=flag
                ).pack(),
            )
        )
        cancel_row.append(InlineKeyboardButton(text=" ", callback_data=self.ignore_callback))
        cancel_row.append(
            InlineKeyboardButton(
                text=self._labels.today_caption,
                callback_data=SimpleCalendarCallback(
                    act=SimpleCalAct.today, year=year, month=month, day=day, flag=flag
                ).pack(),
            )
        )
        kb.append(cancel_row)
        return InlineKeyboardMarkup(row_width=7, inline_keyboard=kb)

    async def _update_calendar(self, query: CallbackQuery, with_date: datetime, flag):
        await query.message.edit_reply_markup(
            reply_markup=await self.start_calendar(int(with_date.year), int(with_date.month), flag)
        )

    async def process_selection(self, query: CallbackQuery, data: SimpleCalendarCallback, flag) -> tuple:
        """
        Process the callback_query. This method generates a new calendar if forward or
        backward is pressed. This method should be called inside a CallbackQueryHandler.
        :param query: callback_query, as provided by the CallbackQueryHandler
        :param data: callback_data, dictionary, set by calendar_callback
        :return: Returns a tuple (Boolean,datetime), indicating if a date is selected
                    and returning the date if so.
        """
        return_data = (False, None, None)

        # processing empty buttons, answering with no action
        if data.act == SimpleCalAct.ignore:
            await query.answer(cache_time=60)
            return return_data

        temp_date = datetime(int(data.year), int(data.month), 1)

        # user picked a day button, return date
        if data.act == SimpleCalAct.day:
            return await self.process_day_select(data, query, flag)

        # user navigates to previous year, editing message with new calendar
        if data.act == SimpleCalAct.prev_y:
            prev_date = datetime(int(data.year) - 1, int(data.month), 1)
            await self._update_calendar(query, prev_date, flag)
        # user navigates to next year, editing message with new calendar
        if data.act == SimpleCalAct.next_y:
            next_date = datetime(int(data.year) + 1, int(data.month), 1)
            await self._update_calendar(query, next_date, flag)
        # user navigates to previous month, editing message with new calendar
        if data.act == SimpleCalAct.prev_m:
            prev_date = temp_date - timedelta(days=1)
            await self._update_calendar(query, prev_date, flag)
        # user navigates to next month, editing message with new calendar
        if data.act == SimpleCalAct.next_m:
            next_date = temp_date + timedelta(days=31)
            await self._update_calendar(query, next_date, flag)
        if data.act == SimpleCalAct.today:
            next_date = datetime.now()
            if next_date.year != int(data.year) or next_date.month != int(data.month):
                await self._update_calendar(query, datetime.now(), flag)
            else:
                await query.answer(cache_time=60)
        if data.act == SimpleCalAct.cancel:
            await query.message.delete_reply_markup()
        # at some point user clicks DAY button, returning date
        return return_data

__author__ = 'dvpermyakov'

from datetime import datetime, date, time
import calendar

PROJECT_STARTING_YEAR = 2014


def suitable_date(day, month, year, beginning):
    if not year:
        month = 0
    if not month:
        day = 0
    if not beginning:
        if not year:
            year = datetime.now().year
        if not month:
            month = 12
        if not day:
            day = calendar.monthrange(year, month)[1]
        day = min(day, calendar.monthrange(year, month)[1])
        return datetime.combine(date(year, month, day), time.max)
    else:
        if not year:
            year = PROJECT_STARTING_YEAR
        if not month:
            month = 1
        if not day:
            day = 1
        day = min(day, calendar.monthrange(year, month)[1])
        return datetime.combine(date(year, month, day), time.min)


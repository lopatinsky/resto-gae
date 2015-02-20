__author__ = 'dvpermyakov'


def is_datetime_valid(working_days, working_hours, datetime_for_check):
    working_days = working_days.split(',')
    working_hours = [s.split("-") for s in working_hours.split(',')]
    schedule = {
        int(day): [int(hours) for hours in working_hours[i]]
        for i in xrange(len(working_days)) for day in working_days[i]
    }
    week_day = datetime_for_check.isoweekday()
    hour_for_check = datetime_for_check.hour
    start_hour = schedule[week_day][0]
    end_hour = schedule[week_day][1]
    if start_hour < hour_for_check < end_hour:
        return True
    else:
        return False
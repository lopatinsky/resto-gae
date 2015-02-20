__author__ = 'dvpermyakov'

import logging


def is_datetime_valid(schedule_list, datetime_for_check):
    week_day = datetime_for_check.isoweekday()
    hour_for_check = int(datetime_for_check.hour)

    start_hour = None
    end_hour = None
    for schedule in schedule_list:
        if week_day in schedule['days']:
            start_hour = int(schedule['hours'].split('-')[0])
            end_hour = int(schedule['hours'].split('-')[1])
            break

    if not start_hour:
        logging.info('what?')
        return False

    if start_hour < hour_for_check < end_hour:
        return True
    else:
        logging.info('%s<%s<%s' % start_hour, hour_for_check, end_hour)
        return False
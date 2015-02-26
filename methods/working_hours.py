__author__ = 'dvpermyakov'

import logging


def is_datetime_valid(schedule_list, datetime_for_check):
    week_day = datetime_for_check.isoweekday()
    start_hour, end_hour = parse_company_schedule(schedule_list, week_day)

    hour_for_check = int(datetime_for_check.hour)

    if start_hour is None or end_hour is None:
        return True

    if start_hour >= end_hour:
        end_hour += 24

    if hour_for_check > start_hour:
        hour_for_check += 24

    if start_hour < hour_for_check < end_hour:
        return True
    else:
        logging.info('%s<%s<%s' % (start_hour, hour_for_check, end_hour))
        return False


def parse_company_schedule(schedule_list, week_day):
    logging.info(schedule_list)

    start_hour = None
    end_hour = None
    for schedule in schedule_list:
        if week_day in schedule['days']:
            start_hour = int(schedule['hours'].split('-')[0])
            end_hour = int(schedule['hours'].split('-')[1])
            break

    return start_hour, end_hour
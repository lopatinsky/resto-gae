# coding=utf-8
import datetime

__author__ = 'dvpermyakov'

import logging


def _date_str_to_date(date_str):
    year, month, date = int(date_str[:4]), int(date_str[4:6]), int(date_str[6:])
    return datetime.date(year, month, date)


def _parse_overrides(overrides):
    overrides_dict = {}
    if overrides:
        for override in overrides.split(';'):
            dates_str, hours_str = override.split(':')
            hours = [int(h) for h in hours_str.split('-')] if hours_str else None

            if '-' not in dates_str:
                dates_str += '-' + dates_str
            date_start_str, date_end_str = dates_str.split('-')
            date_start, date_end = _date_str_to_date(date_start_str), _date_str_to_date(date_end_str)

            while date_start <= date_end:
                overrides_dict[date_start] = hours
                date_start += datetime.timedelta(days=1)
    return overrides_dict


def is_datetime_valid(schedule_list, datetime_for_check, is_delivery, overrides=None):
    start_hour, end_hour = parse_company_schedule(schedule_list, datetime_for_check.date(), is_delivery, overrides)

    hour_for_check = int(datetime_for_check.hour)

    if start_hour is None or end_hour is None:
        return True

    if start_hour >= end_hour:
        end_hour += 24

    if hour_for_check > end_hour:
        hour_for_check += 24

    if start_hour <= hour_for_check < end_hour:
        return True
    else:
        logging.info('%s<=%s<%s' % (start_hour, hour_for_check, end_hour))
        return False


def parse_company_schedule(schedule_list, date, for_delivery=False, overrides=None):
    logging.info(schedule_list)

    overrides_dict = _parse_overrides(overrides)
    logging.warn('parsed overrides %s', overrides_dict)

    start_hour = None
    end_hour = None
    if date in overrides_dict:
        logging.debug('date %s in overrides', date)
        hrs = overrides_dict[date]
        if not hrs:
            return 24, 0
        start_hour, end_hour = hrs
    else:
        logging.debug('date %s not in overrides', date)
        for schedule in schedule_list:
            if date.isoweekday() in schedule['days']:
                start_hour = int(schedule['hours'].split('-')[0])
                end_hour = int(schedule['hours'].split('-')[1])
                break

    if for_delivery:
        # adding one additional hour at open and close time
        # e.g. if schedule is 11-23, allow to order for 12-24
        start_hour += 1
        end_hour += 1

    return start_hour, end_hour

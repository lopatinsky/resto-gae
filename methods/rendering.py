from datetime import datetime, timedelta, time

__author__ = 'dvpermyakov'


def timestamp(datetime_object):
    return int(time.mktime(datetime_object.timetuple()))


def parse_iiko_time(time_str, company):
    return datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S") - timedelta(seconds=company.get_timezone_offset())
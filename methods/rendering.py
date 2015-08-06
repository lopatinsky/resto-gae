from datetime import datetime, timedelta

__author__ = 'dvpermyakov'


def parse_iiko_time(time_str, company):
    return datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S") - timedelta(seconds=company.get_timezone_offset())
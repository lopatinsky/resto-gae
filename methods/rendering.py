from datetime import datetime, timedelta, time

__author__ = 'dvpermyakov'


def timestamp(datetime_object):
    return int(time.mktime(datetime_object.timetuple()))


def parse_iiko_time(time_str, company):
    return datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S") - timedelta(seconds=company.get_timezone_offset())


def filter_phone(phone):
    phone = ''.join(c for c in phone if '0' <= c <= '9')
    if len(phone) == 10 and phone[0] != '7':
        phone = '7' + phone
    elif len(phone) == 11 and phone[0] == '8':
        phone = '7' + phone[1:]
    if len(phone) != 11 or phone[0] not in '78':
        return None
    return '+' + phone


def parse_str_date(str_date):
    try:
        try:
            date = datetime.strptime(str_date, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            date = datetime.strptime(str_date, '%Y-%m-%d %I:%M:%S %p')
    except ValueError:
        date = None
    return date

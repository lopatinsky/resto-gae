# coding=utf-8
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


def prepare_address(order):
    if not order.address.get('comment'):
        order.address['comment'] = u''
    if order.address.get('home') and len(order.address['home']) > 10:
        order.address['comment'] += u' Дом: %s' % order.address['home']
        order.address['home'] = '0'
    if order.address.get('housing') and len(order.address['housing']) > 10:
        order.address['comment'] += u' Корпус: %s' % order.address['housing']
        order.address['housing'] = ''
    if order.address.get('apartment') and len(order.address['apartment']) > 10:
        order.address['comment'] += u' Квартира: %s' % order.address['apartment']
        order.address['apartment'] = ''
    if order.address.get('entrance') and len(order.address['entrance']) > 10:
        order.address['comment'] += u' Подъезд: %s' % order.address['entrance']
        order.address['entrance'] = ''
    if order.address.get('floor') and len(order.address['floor']) > 10:
        order.address['comment'] += u' Этаж: %s' % order.address['floor']
        order.address['floor'] = ''
    if order.address.get('doorphone') and len(order.address['doorphone']) > 10:
        order.address['comment'] += u' Подъезд: %s' % order.address['doorphone']
        order.address['doorphone'] = ''


def parse_str_date(str_date):
    try:
        try:
            date = datetime.strptime(str_date, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            date = datetime.strptime(str_date, '%Y-%m-%d %I:%M:%S %p')
    except ValueError:
        date = None
    return date

# coding=utf-8

import json
import logging
from google.appengine.api import urlfetch
from models.iiko.customer import IOS_DEVICE, ANDROID_DEVICE

parse_acc = {
    'rest_api_key': 'vN10st4XD2AD5gF8ziKCgWbo6tyLNE2scmRaXglU',
    'application_id': '8EdzRDGVxjOqnHzv7WU7S6XbhIUBsgzqPk6ax77m'
}

parce_acc_another = {
    'rest_api_key': 'uDd0iYV75BZylEq4UGIpEu6252590YwBeyCHjNIN',
    'application_id': 'uXhll3SYelAB6GEBwV81YFk3EuqUAB0fvTuh0Qm4'
}

DEVICE_TYPE_MAP = {
    IOS_DEVICE: 'ios',
    ANDROID_DEVICE: 'android'
}


GENERAL_TYPE = 0
ORDER_INFO_TYPE = 1
ORDER_SCREEN_TYPE = 2
REVIEW_TYPE = 3
PUSH_TYPES = (GENERAL_TYPE, ORDER_INFO_TYPE, ORDER_SCREEN_TYPE, REVIEW_TYPE)


def send_push(channels, data, device_type, order=None):
    another_companies = ['107662a7-39d5-11e5-80c1-d8d385655247']

    if device_type not in DEVICE_TYPE_MAP:
        logging.error('Has not device type')
        return

    payload = {
        'channels': channels,
        'type': DEVICE_TYPE_MAP[device_type],
        'data': data
    }
    app_id = parse_acc['application_id']
    api_key = parse_acc['rest_api_key']
    if order and order.venue_id in another_companies:
        app_id = parce_acc_another['application_id']
        api_key = parce_acc_another['rest_api_key']
    headers = {
        'Content-Type': 'application/json',
        'X-Parse-Application-Id': app_id,
        'X-Parse-REST-API-Key': api_key
    }
    result = urlfetch.fetch('https://api.parse.com/1/push', payload=json.dumps(payload), method='POST',
                            headers=headers, validate_certificate=False, deadline=10).content
    logging.info(payload)
    logging.info(result)
    return json.loads(result)


def make_general_push_data(text, device, head=None):
    data = None
    if device == ANDROID_DEVICE:
        data = {
            'head': head if head else '',
            'text': text,
            'action': 'com.empatika.iiko'
        }
    elif device == IOS_DEVICE:
        data = {
            'alert': text
        }
    return data


def _make_order_push_data(order, customer):
    text = u'Статус заказа №%s был изменен на %s' % (order.number, order.PUSH_STATUSES[order.status])
    head = u'Заказ №%s' % order.number
    data = {
        'type': ORDER_INFO_TYPE,
        'order_id': order.order_id,
        'order_status': order.status
    }
    data.update(make_general_push_data(text, customer.get_device(), head))
    return data


def _make_order_review_data(order, customer):
    text = u'Оцените заказ'
    data = {
        'type': REVIEW_TYPE,
        'review': {
            'order_id': order.order_id
        }
    }
    data.update(make_general_push_data(text, customer.get_device()))
    return data


def _make_order_screen_data(customer, text):
    data = {
        'type': ORDER_SCREEN_TYPE,
    }
    data.update(make_general_push_data(text, customer.get_device()))
    return data


def make_mass_push_data(text, full_text, device, head=None):
    data = {
        'type': GENERAL_TYPE,
        'popup_text': full_text
    }
    data.update(make_general_push_data(text, device, head))
    return data


def send_order_status_push(order):
    customer = order.customer.get()
    data = _make_order_push_data(order, customer)
    send_push(channels=["order_%s" % order.order_id], data=data, device_type=customer.get_device(), order=order)


def send_order_review_push(order):
    customer = order.customer.get()
    data = _make_order_review_data(order, customer)
    send_push(["order_%s" % order.order_id], data=data, device_type=customer.get_device(), order=order)


def send_order_screen_push(order, text):
    customer = order.customer.get()
    data = _make_order_screen_data(customer, text)
    send_push(["order_%s" % order.order_id], data=data, device_type=customer.get_device(), order=order)
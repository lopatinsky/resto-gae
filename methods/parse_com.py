# coding=utf-8

import json
import logging
from google.appengine.api import urlfetch
from models.iiko.customer import IOS_DEVICE, ANDROID_DEVICE

parse_acc = {
    'master_key': 'YaEHCHCURT6qQFYwvWeTsIwho6cJPSDBhDAz4CS1',
    'client_key': 'CSxzgKDGJwUv7GVySEpkti7nOiHYFJMHR3RYxnU0',
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


def make_order_push_data(order_id, order_number, order_status, order_status_description, device):
    format_string = u'Статус заказа №{0} был изменен на {1}'
    message = format_string.format(order_number, order_status_description)
    head = u'Заказ №%s' % order_number
    data = {
        'order_id': order_id,
        'order_status': order_status
    }
    data.update(make_general_push_data(message, device, head))
    return data


def make_mass_push_data(text, full_text, device, head=None):
    data = {
        'popup_text': full_text
    }
    data.update(make_general_push_data(text, device, head))
    return data


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
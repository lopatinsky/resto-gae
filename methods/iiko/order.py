# coding=utf-8
from datetime import timedelta
import json
import logging
from methods.iiko.base import post_request, get_request
from methods.iiko.promo import get_iikonet_payment_type
from models.iiko import CompanyNew, DeliveryTerminal

__author__ = 'dvpermyakov'


def prepare_order(order, customer, payment_type):
    company = CompanyNew.get_by_iiko_id(order.venue_id)
    local_date = order.date + timedelta(seconds=company.get_timezone_offset())
    obj = {
        'restaurantId': order.venue_id,
        'customer': {
            'name': customer.name,
            'phone': customer.phone,
        },
        'order': {
            'date': local_date.strftime('%Y-%m-%d %H:%M:%S'),
            'isSelfService': 0 if order.is_delivery else 1,
            'paymentItems': [{
                'paymentType': {
                    'code': '',
                    'name': 'not iiko.Net'
                },
                'sum': order.sum,
                "combinatable": True,
                'isProcessedExternally': 0
            }],
            'phone': customer.phone,
            'items': order.items,
            'comment': order.comment,
            'address': {
                'home': 0
            }
        }
    }

    if company.is_iiko_system:
        obj['order']['paymentItems'].append({
            "sum": 0.0,
            'paymentType': {
                "code": get_iikonet_payment_type(order),
                "name": "iiko.Net",
                "comment": "",
                "combinatable": True,
            },
            "additionalData": json.dumps({
                "externalIdType": "PHONE",
                "externalId": customer.phone
            }),
            "isProcessedExternally": False,
            "isPreliminary": True,
            "isExternal": True,
        })

    if customer.customer_id:
        obj['customer']['id'] = customer.customer_id

    if not order.is_delivery:
        obj['deliveryTerminalId'] = order.delivery_terminal_id
    else:
        order.delivery_terminal_id = None
        if order.venue_id == CompanyNew.ORANGE_EXPRESS:
            dt_mapping = {
                u"Одинцово": "2b20fde1-727f-e430-013e-203bb2e09905",
                u"Егорьевск": "7658baf0-cc65-28b5-014b-7cde6614cfbe",
                u"Подольск": "e0a67a59-c018-2c9c-0149-893d7b97148e",
                u"Климовск": "e0a67a59-c018-2c9c-0149-893d7b97148e",
                u"Домодедово": "2d163ab4-ce5d-e5cf-014b-84e547cfdf79"
            }
            obj['deliveryTerminalId'] = dt_mapping[order.address['city']]
        elif order.venue_id == CompanyNew.DIMASH:
            obj['deliveryTerminalId'] = DeliveryTerminal.get_any(order.venue_id).key.id()
        elif order.venue_id == CompanyNew.PANDA:
            #obj['deliveryTerminalId'] = "9d55b8d9-7b71-aa53-0144-4da56c249760"  # DOSTAVKA48
            obj['deliveryTerminalId'] = "12c99191-4e48-67cc-014d-0ef17725d974"  # PANDA

    customer_id = customer.customer_id
    if customer_id:
        obj['customer']['id'] = customer_id

    if order.is_delivery:
        obj['order']['address'] = order.address

    if payment_type:
        typ = company.get_payment_type(payment_type)
        obj['order']['paymentItems'][0]['paymentType']['code'] = typ.iiko_uuid
        if typ.type_id == 2:
            obj['order']['paymentItems'][0].update({
                'isProcessedExternally': True,
                'isExternal': True,
                'isPreliminary': True
            })

    return obj


def pre_check_order(company, order_dict):
    pre_check = post_request(company, '/orders/checkCreate', {
        'requestTimeout': 30
    }, order_dict)
    logging.info(pre_check)
    return json.loads(pre_check)


def place_order(company, order_dict):
    result = post_request(company, '/orders/add', {
        'requestTimeout': 30
    }, order_dict)
    logging.info(result)
    return json.loads(result)


def order_info(order):
    company = CompanyNew.get_by_iiko_id(order.venue_id)
    result = get_request(company, '/orders/info', {
        'requestTimeout': 30,
        'organization': order.venue_id,
        'order': order.order_id
    })
    return json.loads(result)


def order_info1(order_id, org_id):
    company = CompanyNew.get_by_iiko_id(org_id)
    result = get_request(company, '/orders/info', {
        'requestTimeout': 30,
        'organization': org_id,
        'order': order_id
    })
    logging.info(result)
    return json.loads(result)

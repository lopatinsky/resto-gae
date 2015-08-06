import json
from methods.iiko.base import __get_request

__author__ = 'dvpermyakov'


def get_delivery_terminals(company):
    result = __get_request(company, '/deliverySettings/getDeliveryTerminals', {
        'organization': company.iiko_org_id
    })
    return json.loads(result)['deliveryTerminals']
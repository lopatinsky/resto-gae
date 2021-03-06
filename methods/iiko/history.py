import json
from datetime import timedelta
from methods.iiko.base import get_request
from models.iiko import CompanyNew

__author__ = 'dvpermyakov'


def get_history(client_id, org_id):
    company = CompanyNew.get_by_iiko_id(org_id)
    result = get_request(company, '/orders/deliveryHistory', {
        'organization': org_id,
        'customer': client_id,
        'requestTimeout': 20
    })
    obj = json.loads(result)
    return obj


def get_history_by_phone(phone, org_id):
    company = CompanyNew.get_by_iiko_id(org_id)
    result = get_request(company, '/orders/deliveryHistoryByPhone', {
        'organization': org_id,
        'phone': phone
    })
    obj = json.loads(result)
    return obj


def get_orders(company, start, end, status=None):
    payload = {
        'organization': company.iiko_org_id,
        'dateFrom': start.strftime("%Y-%m-%d"),
        'dateTo': end.strftime("%Y-%m-%d"),
        'request_timeout': '00:01:00'
    }
    if status:
        payload['deliveryStatus'] = status
    return json.loads(get_request(company, '/orders/deliveryOrders', payload, deadline=45))

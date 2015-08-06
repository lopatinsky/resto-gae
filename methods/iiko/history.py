import json
from datetime import timedelta
from methods.iiko.base import __get_request
from models.iiko import CompanyNew

__author__ = 'dvpermyakov'


def get_history(client_id, org_id):
    company = CompanyNew.get_by_iiko_id(org_id)
    result = __get_request(company, '/orders/deliveryHistory', {
        'organization': org_id,
        'customer': client_id,
        'requestTimeout': 20
    })
    obj = json.loads(result)
    return obj


def get_history_by_phone(phone, org_id):
    company = CompanyNew.get_by_iiko_id(org_id)
    result = __get_request(company, '/orders/deliveryHistoryByPhone', {
        'organization': org_id,
        'phone': phone
    })
    obj = json.loads(result)
    return obj


def get_orders(company, start, end, status=None):
    start += timedelta(seconds=company.get_timezone_offset())
    end += timedelta(seconds=company.get_timezone_offset())
    payload = {
        'organization': company.iiko_org_id,
        'dateFrom': start.strftime("%Y-%m-%d %H:%M:%S"),
        'dateTo': end.strftime("%Y-%m-%d %H:%M:%S"),
        'requestTimeout': 20
    }
    if status:
        payload['deliveryStatus'] = status
    return json.loads(__get_request(company, '/orders/deliveryOrders', payload))

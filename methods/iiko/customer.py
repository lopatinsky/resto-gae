import json
from methods.iiko.base import __get_request, __post_request

__author__ = 'dvpermyakov'


def get_customer_by_phone(company, phone):
    result = __get_request(company, '/customers/get_customer_by_phone', {
        'organization': company.iiko_org_id,
        'phone': phone
    }, force_platius=True)
    return json.loads(result)


def get_customer_by_id(company, customer_id):
    result = __get_request(company, '/customers/get_customer_by_id', {
        'organization': company.iiko_org_id,
        'id': customer_id
    }, force_platius=True)
    return json.loads(result)


def get_customer_by_card(company, card):
    result = __get_request(company, '/customers/get_customer_by_card', {
        'organization': company.iiko_org_id,
        'card': card
    }, force_platius=True)
    return json.loads(result)


def create_or_update_customer(company, data):
    result = __post_request(company, '/customers/create_or_update', {
        'organization': company.iiko_org_id
    }, {'customer': data}, force_platius=True)
    return result.strip('"')
import json
from methods.iiko.base import __get_request
from models.iiko import CompanyNew

__author__ = 'dvpermyakov'


def get_orgs(iiko_api_login, new_endpoints):
    dummy = CompanyNew(iiko_login=iiko_api_login, new_endpoints=new_endpoints)
    result = __get_request(dummy, '/organization/list', {})
    return json.loads(result)


def get_org(iiko_api_login, org_id, new_endpoints):
    dummy = CompanyNew(iiko_login=iiko_api_login, new_endpoints=new_endpoints)
    result = __get_request(dummy, '/organization/%s' % org_id, {})
    return json.loads(result)


def get_payment_types(org_id):
    company = CompanyNew.get_by_iiko_id(org_id)
    result = __get_request(company, '/paymentTypes/getPaymentTypes', {
        'organization': org_id
    })
    obj = json.loads(result)
    return obj
import json
from methods.iiko.base import get_request
from models.iiko.company import CompanyNew

__author__ = 'dvpermyakov'


def _get_dummy_company(iiko_api_login, new_endpoints):
    return CompanyNew(
        iiko_login=iiko_api_login,
        platius_login=iiko_api_login,
        iiko_org_id='00000000-0000-0000-0000-000000000000',
        platius_org_id='00000000-0000-0000-0000-000000000000',
        new_endpoints=new_endpoints
    )


def get_orgs(iiko_api_login, new_endpoints):
    dummy = _get_dummy_company(iiko_api_login, new_endpoints)
    result = get_request(dummy, '/organization/list', {})
    return json.loads(result)


def get_org(iiko_api_login, org_id, new_endpoints):
    dummy = _get_dummy_company(iiko_api_login, new_endpoints)
    result = get_request(dummy, '/organization/%s' % org_id, {})
    return json.loads(result)


def get_payment_types(org_id):
    company = CompanyNew.get_by_iiko_id(org_id)
    result = get_request(company, '/paymentTypes/getPaymentTypes', {
        'organization': org_id
    })
    obj = json.loads(result)
    return obj

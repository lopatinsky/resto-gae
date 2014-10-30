import json
import logging
import urllib
from google.appengine.api import urlfetch

ALFA_BASE_URL = 'https://test.paymentgate.ru/testpayment'


def __post_request_alfa(api_path, params):
    url = '%s%s' % (ALFA_BASE_URL, api_path)
    payload = json.dumps(params)
    logging.info(payload)
    if params:
        url = '%s?%s' % (url, urllib.urlencode(params))
    logging.info(url)
    return urlfetch.fetch(url, method='POST', headers={'Content-Type': 'application/json'}, deadline=30, validate_certificate=False).content


def tie_card(company, amount, orderNumber, returnUrl, client_id, pageView):
    p = {
        'userName': company.alpha_login,
        'password': company.alpha_pass,
        'amount': amount,
        'orderNumber': orderNumber,
        'returnUrl': returnUrl,
        'clientId': client_id,
        'pageView': pageView
    }
    result = __post_request_alfa('/rest/registerPreAuth.do', p)
    return json.loads(result)


def check_status(company, order_id):
    params = {
        'userName': company.alpha_login,
        'password': company.alpha_pass,
        'orderId': order_id
    }
    result = __post_request_alfa('/rest/getOrderStatus.do', params)
    return json.loads(result)


def get_back_blocked_sum(company, order_id):
    params = {
        'userName': company.alpha_login,
        'password': company.alpha_pass,
        'orderId': order_id
    }
    result = __post_request_alfa('/rest/reverse.do', params)
    return json.loads(result)


def create_pay(company, binding_id, order_id):
    params = {
        'userName': company.alpha_login,
        'password': company.alpha_pass,
        'mdOrder': order_id,
        'bindingId': binding_id
    }
    result = __post_request_alfa('/rest/paymentOrderBinding.do', params)
    return json.loads(result)


def pay_by_card(company, order_id, amount):
    params = {
        'userName': company.alpha_login,
        'password': company.alpha_pass,
        'orderId': order_id,
        'amount': amount
    }
    result = __post_request_alfa('/rest/deposit.do', params)
    return json.loads(result)


def unbind_card(company, binding_id):
    params = {
        'userName': company.alpha_login,
        'password': company.alpha_pass,
        'bindingId': binding_id
    }
    result = __post_request_alfa('/rest/unBindCard.do', params)
    return json.loads(result)

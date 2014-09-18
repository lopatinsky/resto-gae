import json
import logging
import urllib
from google.appengine.api import urlfetch

ALFA_BASE_URL = 'https://test.paymentgate.ru/testpayment'

ALFA_LOGIN = 'empatika_autopay-api'
ALFA_PASSWORD = 'empatika_autopay'


def __post_request_alfa(api_path, params):
    url = '%s%s' % (ALFA_BASE_URL, api_path)
    payload = json.dumps(params)
    logging.info(payload)
    if params:
        url = '%s?%s' % (url, urllib.urlencode(params))
    logging.info(url)
    return urlfetch.fetch(url, method='POST', headers={'Content-Type': 'application/json'}, deadline=30, validate_certificate=False).content


def tie_card(amount, orderNumber, returnUrl, client_id, pageView):
    p = {
        'userName': ALFA_LOGIN,
        'password': ALFA_PASSWORD,
        'amount': amount,
        'orderNumber': orderNumber,
        'returnUrl': returnUrl,
        'clientId': client_id,
        'pageView': pageView
    }
    result = __post_request_alfa('/rest/registerPreAuth.do', p)
    return json.loads(result)


def check_status(order_id):
    params = {
        'userName': ALFA_LOGIN,
        'password': ALFA_PASSWORD,
        'orderId': order_id
    }
    result = __post_request_alfa('/rest/getOrderStatus.do', params)
    return json.loads(result)


def get_back_blocked_sum(order_id):
    params = {
        'userName': ALFA_LOGIN,
        'password': ALFA_PASSWORD,
        'orderId': order_id
    }
    result = __post_request_alfa('/rest/reverse.do', params)
    return json.loads(result)


def create_pay(binding_id, order_id):
    params = {
        'userName': ALFA_LOGIN,
        'password': ALFA_PASSWORD,
        'mdOrder': order_id,
        'bindingId': binding_id
    }
    result = __post_request_alfa('/rest/paymentOrderBinding.do', params)
    return json.loads(result)


def pay_by_card(order_id, amount):
    params = {
        'userName': ALFA_LOGIN,
        'password': ALFA_PASSWORD,
        'orderId': order_id,
        'amount': amount
    }
    result = __post_request_alfa('/rest/deposit.do', params)
    return json.loads(result)


def unbind_card(binding_id):
    params = {
        'userName': ALFA_LOGIN,
        'password': ALFA_PASSWORD,
        'bindingId': binding_id
    }
    result = __post_request_alfa('/rest/unBindCard.do', params)
    return json.loads(result)

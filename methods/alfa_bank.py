# coding=utf-8

import json
import logging
import urllib
from google.appengine.api import urlfetch
from config import config


ALPHA_CARD_LIMIT_CODES = [-20010, 902, 116, 123]
ALPHA_WRONG_CREDENTIALS_CODES = [71015]
CARD_LIMIT_CODE = 1
CARD_WRONG_CREDENTIALS_CODE = 2


def __post_request_alfa(api_path, params):
    url = '%s%s' % (config.ALFA_BASE_URL, api_path)
    payload = json.dumps(params)
    logging.info(payload)
    if params:
        url = '%s?%s' % (url, urllib.urlencode(params))
    logging.info(url)
    return urlfetch.fetch(url, method='POST', headers={'Content-Type': 'application/json'}, deadline=30,
                          validate_certificate=False).content


def tie_card(company, amount, order_number, return_url, client_id, page_view):
    p = {
        'userName': company.alpha_login,
        'password': company.alpha_pass,
        'amount': amount,
        'orderNumber': order_number,
        'returnUrl': return_url,
        'clientId': client_id,
        'pageView': page_view
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


def check_extended_status(company, order_id):
    params = {
        'userName': company.alpha_login,
        'password': company.alpha_pass,
        'orderId': order_id,
    }
    result = __post_request_alfa('/rest/getOrderStatusExtended.do', params)
    result_json = json.loads(result)
    if result_json['actionCode'] in ALPHA_CARD_LIMIT_CODES:
        status_code = CARD_LIMIT_CODE
    elif result_json['actionCode'] in ALPHA_WRONG_CREDENTIALS_CODES:
        status_code = CARD_WRONG_CREDENTIALS_CODE
    else:
        status_code = result_json['actionCode']
    return {
        'error_code': status_code,
        'description': result_json['actionCodeDescription'],
        'alfa_response': result_json
    }


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

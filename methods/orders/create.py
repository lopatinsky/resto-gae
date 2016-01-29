# coding=utf-8
import time
import logging
import re
from methods.alfa_bank import get_bindings, tie_card, create_pay, check_extended_status

__author__ = 'dvpermyakov'


def check_binding_id(company, alpha_client_id, binding_id):
    # todo android binding_id fuckup
    if not re.match('\w{8}-\w{4}-\w{4}-\w{4}-\w{12}$', binding_id):
        logging.info('wrong binding_id: %s', binding_id)
        pan = binding_id[-4:]
        bindings = get_bindings(company, alpha_client_id)
        logging.info('got bindings from alfa: %s', bindings)
        for binding in bindings['bindings']:
            if binding['maskedPan'][-4:] == pan:
                logging.info('found binding: %s', bindings)
                binding_id = binding['bindingId']
                break
        else:
            logging.warning('binding not found')
    return binding_id


def create_payment(company, order, alpha_client_id):
    order_number = order.order_id.replace('-', '')
    result = tie_card(company, int(order.sum * 100), order_number, 'returnUrl', alpha_client_id, 'MOBILE')
    if 'errorCode' not in result or str(result['errorCode']) == '0':
        return True, result['orderId']
    return False, result['errorMessage'] or result['error'] or ''


def perform_payment(company, order, order_dict, payment_id, binding_id):
    create_result = create_pay(company, binding_id, payment_id)
    if str(create_result.get('errorCode')) != '0':
        return False, create_result['errorMessage']

    check_result = check_extended_status(company, payment_id)['alfa_response']
    if str(check_result.get('errorCode')) != '0':
        return False, check_result['errorMessage']

    if not (check_result['actionCode'] == 0 and check_result['orderStatus'] == 1):
        logging.warning("extended status check fail")
        return False, check_result['actionCodeDescription']

    order.comment += u"\nЗаказ оплачен картой через приложение"
    order_dict["order"]["comment"] = order.comment
    return True, payment_id

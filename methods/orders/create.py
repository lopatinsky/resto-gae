# coding=utf-8
import time
import logging
import re
from methods.alfa_bank import get_bindings, tie_card, create_pay, check_extended_status

__author__ = 'dvpermyakov'


def pay_by_card(company, order, order_dict, binding_id, alpha_client_id):
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

    tie_result = tie_card(company, int(order.sum * 100), int(time.time()), 'returnUrl', alpha_client_id,
                          'MOBILE')
    logging.info("registration")
    logging.info(str(tie_result))
    if 'errorCode' not in tie_result.keys() or str(tie_result['errorCode']) == '0':
        order_id = tie_result['orderId']
        create_result = create_pay(company, binding_id, order_id)
        logging.info("block")
        logging.info(str(create_result))
        if 'errorCode' not in create_result.keys() or str(create_result['errorCode']) == '0':
            status_check_result = check_extended_status(company, order_id)['alfa_response']
            logging.info("status check")
            logging.info(str(status_check_result))
            if str(status_check_result.get('errorCode')) == '0' and \
                    status_check_result['actionCode'] == 0 and status_check_result['orderStatus'] == 1:
                # payment succeeded
                order.comment += u"\nЗаказ оплачен картой через приложение"
                order_dict["order"]["comment"] = order.comment
                return True, order_id
    return False, None

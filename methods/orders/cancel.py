import logging
from methods.alfa_bank import get_back_blocked_sum
from methods.parse_com import send_order_status_push
from models.iiko import CompanyNew

__author__ = 'dvpermyakov'


def cancel(order):
    company = CompanyNew.get_by_iiko_id(order.venue_id)
    cancel_result = get_back_blocked_sum(company, order.alfa_order_id)
    logging.info("cancel %s" % str(cancel_result))
    success = 'errorCode' not in cancel_result or str(cancel_result['errorCode']) == '0'
    if not success:
        logging.warning("cancel failed")
        return
    send_order_status_push(order)

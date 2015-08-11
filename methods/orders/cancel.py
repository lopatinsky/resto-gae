import logging
from methods.alfa_bank import get_back_blocked_sum
from methods.auto.request import cancel_oder
from methods.parse_com import send_order_status_push
from models.auto import AutoVenue
from models.iiko import CompanyNew, DeliveryTerminal

__author__ = 'dvpermyakov'


def cancel(order):
    company = CompanyNew.get_by_iiko_id(order.venue_id)
    if order.delivery_terminal_id:
        delivery_terminal = DeliveryTerminal.get_by_id(order.delivery_terminal_id)
        auto_venue = AutoVenue.query(AutoVenue.delivery_terminal == delivery_terminal.key).get()
    else:
        auto_venue = None
    if auto_venue:
        cancel_oder(order, auto_venue)
    else:
        cancel_result = get_back_blocked_sum(company, order.alfa_order_id)
        logging.info("cancel %s" % str(cancel_result))
        success = 'errorCode' not in cancel_result or str(cancel_result['errorCode']) == '0'
        if not success:
            logging.warning("cancel failed")
            return
        send_order_status_push(order)

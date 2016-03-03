# coding=utf-8

import logging
from methods.alfa_bank import get_back_blocked_sum
from methods.auto.request import cancel_order
from methods.parse_com import send_order_status_push
from methods.specials import oe_cancel
from models.iiko import CompanyNew, PaymentType
from models.iiko.delivery_terminal import DeliveryTerminal
from models.iiko.order import AUTO_APP_SOURCE

__author__ = 'dvpermyakov'


def cancel(order):
    company = CompanyNew.get_by_iiko_id(order.venue_id)
    if company.auto_token and order.source == AUTO_APP_SOURCE:
        cancel_order(order, company.auto_token)
    if order.venue_id == CompanyNew.ORANGE_EXPRESS:
        oe_cancel.handle_cancel(order)
    else:
        if order.payment_type == PaymentType.CARD:
            delivery_terminal = DeliveryTerminal.get_by_id(order.delivery_terminal_id) \
                if order.delivery_terminal_id else None
            cancel_result = get_back_blocked_sum(company, delivery_terminal, order.alfa_order_id)
            logging.info("cancel %s" % str(cancel_result))
            success = 'errorCode' not in cancel_result or str(cancel_result['errorCode']) == '0'
            if not success:
                logging.warning("cancel failed")
                return
        send_order_status_push(order)

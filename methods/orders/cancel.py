# coding=utf-8

import logging
from methods.alfa_bank import get_back_blocked_sum
from methods.auto.request import cancel_oder
from methods.email import mandrill
from methods.parse_com import send_order_status_push
from models.auto import AutoVenue
from models.iiko import CompanyNew, DeliveryTerminal, PaymentType

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
    if order.payment_type == PaymentType.CARD:
        if order.venue_id == CompanyNew.ORANGE_EXPRESS:
            customer = order.customer.get()
            message = u"№ заказа: %s<br/>" \
                      u"Сумма: %s<br/>" \
                      u"Клиент: %s %s<br/>" \
                      u"ID платежа: %s" % (order.number, order.initial_sum, customer.phone, customer.name, order.alfa_order_id)
            mandrill.send_email("noreply-order@ru-beacon.ru",
                                ["kapus78@mail.ru"],
                                ["mdburshteyn@gmail.com", "isparfenov@gmail.com"],
                                u"[ОЭ] Отмена заказа с безналичной оплатой",
                                message)
        else:
            cancel_result = get_back_blocked_sum(company, order.alfa_order_id)
            logging.info("cancel %s" % str(cancel_result))
            success = 'errorCode' not in cancel_result or str(cancel_result['errorCode']) == '0'
            if not success:
                logging.warning("cancel failed")
                return
    send_order_status_push(order)

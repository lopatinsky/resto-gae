# coding=utf-8
import logging
from datetime import date
from google.appengine.ext import deferred

from methods.email import mandrill
from methods.email.admin import send_error
from methods.iiko.history import get_orders
from methods.parse_com import send_order_status_push
from models.iiko.company import CompanyNew, PaymentType
from models.iiko.order import Order


def _handle(order_id):
    from methods.orders.change import do_load

    order = Order.order_by_id(order_id)
    logging.info('searching for move, number %s, id %s', order.number, order.order_id)
    try:
        customer = order.customer.get()
        company = CompanyNew.get_by_iiko_id(order.venue_id)
        orders = get_orders(company, date.today(), date.today())
        for iiko_order in orders['deliveryOrders']:
            if iiko_order['number'] == order.number \
                    and iiko_order['customer']['phone'][-10:] == customer.phone[-10:] \
                    and Order.parse_status(iiko_order['status']) != Order.CANCELED:
                logging.info("found move: %s" % iiko_order['orderId'])
                logging.info(iiko_order)
                order.order_id = iiko_order['orderId']
                do_load(order, order.order_id, order.venue_id, iiko_order)
                send_error("oe_move", "OE move checker: success %s" % order.number, "")
                break
        else:
            send_error("oe_move", "OE move checker: not found %s" % order.number, "")
            if order.payment_type == PaymentType.CARD:
                message = u"№ заказа: %s<br/>" \
                          u"Сумма: %s<br/>" \
                          u"Клиент: %s %s<br/>" \
                          u"ID платежа: %s" % (order.number, order.initial_sum, customer.phone, customer.name, order.alfa_order_id)
                mandrill.send_email("noreply-order@ru-beacon.ru",
                                    ["kapus78@mail.ru"],
                                    ["mdburshteyn@gmail.com", "isparfenov@gmail.com"],
                                    u"[ОЭ] Отмена заказа с безналичной оплатой",
                                    message)
            send_order_status_push(order)
    except Exception as e:
        send_error("oe_move", "OE move checker: exception on %s" % order.number, repr(e))


def handle_cancel(order):
    deferred.defer(_handle, order.order_id)

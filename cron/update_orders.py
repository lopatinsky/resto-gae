# coding=utf-8

import logging

import webapp2

from models.iiko import Order, Venue, Company
from methods import iiko_api
from methods.alfa_bank import get_back_blocked_sum, pay_by_card
from methods.parse_com import send_push


STATUS_TEXTS = {
    Order.UNKNOWN: u"Неизвестно",
    Order.NOT_APPROVED: u"Ожидает подтверждения",
    Order.APPROVED: u"Подтвержден",
    Order.CANCELED: u"Отменен",
    Order.CLOSED: u"Выполнен"
}


# TODO rework
class UpdateOrdersHandler(webapp2.RequestHandler):
    def get(self):
        orders = Order.query(Order.status == Order.NOT_APPROVED).fetch(100500)
        orders.extend(Order.query(Order.status == Order.UNKNOWN).fetch(100500))
        orders.extend(Order.query(Order.status == Order.APPROVED).fetch(100500))
        for order in orders:
            try:
                logging.info("order number: %s" % order.number)
                current_status = order.status
                result = iiko_api.order_info(order)
                order.set_status(result['status'])
                logging.info("current_status: %d, new_status: %d" % (current_status, order.status))
                if order.status != current_status:
                    if order.payment_type == '2':
                        logging.info("order paid by card")

                        venue = Venue.venue_by_id(order.venue_id)
                        company = Company.get_by_id(venue.company_id)

                        if order.status == Order.CLOSED:
                            pay_result = pay_by_card(company, order.alfa_order_id, 0)
                            logging.info("pay")
                            logging.info(str(pay_result))
                            if 'errorCode' not in pay_result.keys() or str(pay_result['errorCode']) == '0':
                                logging.info("pay succeeded")
                            else:
                                logging.warning("pay failed")

                        elif order.status == Order.CANCELED:
                            cancel_result = get_back_blocked_sum(company, order.alfa_order_id)
                            logging.info("cancel")
                            logging.info(str(cancel_result))
                            if 'errorCode' not in cancel_result or str(cancel_result['errorCode']) == '0':
                                logging.info("cancel succeeded")
                            else:
                                logging.warning("cancel failed")

                    data = {'order_id': order.order_id,
                            'order_status': order.status,
                            'action': 'com.empatika.iiko'}
                    format_string = u'Статус заказа №{0} был изменен на {1}'
                    alert_message = format_string.format(order.number, STATUS_TEXTS[order.status])
                    logging.info(alert_message)
                    send_push("order_%s" % order.order_id, alert=alert_message, data=data)
                    order.put()
            except Exception as e:
                logging.exception(e)

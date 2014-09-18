# coding=utf-8

import logging
import webapp2
import iiko
from iiko import Order, PaymentType
from lib.parse_com import send_push

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
                result = iiko.order_info(order)
                order.set_status(result['status'])
                logging.info("current_status: %d, new_status: %d" % (current_status, order.status))
                if order.status != current_status:
                    if order.payment_type == '2':
                        logging.info("order paid by card")
                        if order.status == Order.CLOSED:
                            pay_result = iiko.pay_by_card(order.alfa_order_id, 0)
                            logging.info("pay")
                            logging.info(str(pay_result))
                            if 'errorCode' not in pay_result.keys() or str(pay_result['errorCode']) == '0':
                                logging.info("pay succeeded")
                            else:
                                logging.warning("pay failed")

                        elif order.status == Order.CANCELED:
                            cancel_result = iiko.get_back_blocked_sum(order.alfa_order_id)
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
                    #alert_message = u"\u0421\u0442\u0430\u0442\u0443\u0441 \u0437\u0430\u043a\u0430\u0437\u0430 \u2116{0} \u0431\u044b\u043b \u0438\u0437\u043c\u0435\u043d\u0435\u043d \u043d\u0430 {1}".format(order.number, result['status'])
                    logging.info(alert_message)
                    send_push("order_%s" % order.order_id, alert=alert_message, data=data)
                    order.put()
            except Exception as e:
                logging.exception(e)

        #order = Order.query(Order.order_id == '1c7358fe-3013-4dd9-8bc0-e7342d125e6b').get()
        #order.status = ((order.status + 1 + 1) % 6 - 1)

        #data = {'order_id': order.order_id,
        #        'order_status': order.status}

        #send_push("order_%s" % order.order_id, alert='Status changed', data=data)
        #logging.info('Send push to order_id: %s, status: %d', order.order_id, order.status)
        #order.put()

app = webapp2.WSGIApplication([
    ('/cron/update_orders', UpdateOrdersHandler)
], debug=True)

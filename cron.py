import logging
import webapp2
import iiko
from iiko import Order
from lib.parse_com import send_push

# TODO rework
class UpdateOrdersHandler(webapp2.RequestHandler):
    def get(self):
        orders = Order.query(Order.status == Order.NOT_APPROVED).fetch(100500)
        orders.extend(Order.query(Order.status == Order.UNKNOWN).fetch(100500))
        orders.extend(Order.query(Order.status == Order.APPROVED).fetch(100500))
        for order in orders:
            current_status = order.status
            result = iiko.order_info(order)
            order.set_status(result['status'])
            logging.info("number: %s, current_status: %d, new_status: %d" % (order.number, current_status, order.status))
            if order.status != current_status:
                data = {'order_id': order.order_id,
                        'order_status': order.status}
                #format_string = u'Статус заказа №{0} был изменен на {1}'
                #alert_message = format_string.format(order.number, result['status'])
                alert_message = u"\u0421\u0442\u0430\u0442\u0443\u0441 \u0437\u0430\u043a\u0430\u0437\u0430 \u2116{0} \u0431\u044b\u043b \u0438\u0437\u043c\u0435\u043d\u0435\u043d \u043d\u0430 {1}".format(order.number, result['status'])
                logging.info(alert_message)
                send_push("order_%s" % order.order_id, alert=alert_message, data=data)
                order.put()

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

import logging
import webapp2
import iiko
from iiko import Order
from lib.parse_com import send_push


class UpdateOrdersHandler(webapp2.RequestHandler):
    def get(self):
        orders = Order.query(Order.status == Order.NOT_APPROVED).fetch(100500)
        orders.extend(Order.query(Order.status == Order.APPROVED).fetch(100500))
        for order in orders:
            logging.info(order)
            current_status = order.status
            result = iiko.order_info(order)
            order.set_status(result['status'])
            if order.status != current_status:
                send_push("order_%s" % order.order_id, alert="Status change")
            order.put()

app = webapp2.WSGIApplication([
    ('/cron/update_orders', UpdateOrdersHandler)
], debug=True)

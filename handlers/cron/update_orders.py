# coding=utf-8

import logging
import webapp2
from models.iiko import Order


class UpdateOrdersHandler(webapp2.RequestHandler):
    def get(self):
        orders = Order.query(Order.status < Order.CLOSED).fetch()
        for order in orders:
            try:
                logging.info("order number: %s" % order.number)
                order.reload()
            except Exception as e:
                logging.exception(e)

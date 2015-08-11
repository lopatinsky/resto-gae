# coding=utf-8
from datetime import datetime, timedelta
from google.appengine.ext.deferred import deferred
from webapp2 import RequestHandler
from methods.parse_com import send_order_screen_push
from models.iiko import Order

__author__ = 'dvpermyakov'


class InactiveClientsWithPromo(RequestHandler):
    def get(self):
        start = datetime.utcnow() - timedelta(days=7)
        orders = Order.query(Order.date <= start).fetch()
        text = u'7 дней после заказа'
        for order in orders:
            deferred.defer(send_order_screen_push, order, text)

# coding=utf-8
from datetime import datetime, timedelta
from google.appengine.ext.deferred import deferred
from webapp2 import RequestHandler
from methods.parse_com import send_order_screen_push
from models.iiko import Order

__author__ = 'dvpermyakov'


COMPANIES = ['5cae16f4-4039-11e5-80d2-d8d38565926f']
DAYS = 7


class InactiveClientsWithPromo(RequestHandler):
    def get(self):
        start = datetime.utcnow() - timedelta(days=DAYS+1)
        end = datetime.utcnow() - timedelta(days=DAYS)
        orders = Order.query(Order.date >= start, Order.date <= end).fetch()
        text = u'7 дней после заказа'
        for order in orders:
            if order.venue_id in COMPANIES:
                deferred.defer(send_order_screen_push, order, text)

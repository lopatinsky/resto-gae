# coding=utf-8
import datetime
import time
from ..base import BaseHandler
from models.iiko import Order


class CurrentOrdersHandler(BaseHandler):
    def get(self):
        venue_id = self.request.get('venue_id')
        today = datetime.datetime.combine(datetime.date.today(), datetime.time())
        orders = Order.query(Order.status.IN([Order.NOT_APPROVED, Order.APPROVED]),
                             Order.venue_id == venue_id,
                             Order.date >= today).fetch()

        self.render_json({
            'orders': [order.admin_dict() for order in orders],
            'timestamp': int(time.time())
        })


class OrderUpdatesHandler(BaseHandler):
    def get(self):
        venue_id = self.request.get('venue_id')
        timestamp = self.request.get_range('timestamp')
        orders = Order.query(Order.status.IN([Order.NOT_APPROVED, Order.APPROVED]),
                             Order.venue_id == venue_id,
                             Order.updated >= datetime.datetime.fromtimestamp(timestamp)).fetch()

        self.render_json({
            'orders': [order.admin_dict() for order in orders],
            'timestamp': int(time.time())
        })

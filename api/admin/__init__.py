# coding=utf-8
import datetime
import time
from ..base import BaseHandler
from methods import iiko_api
from models.iiko import Order
from auth import LoginHandler, LogoutHandler


def _build_images_map(venue_id):
    menu = iiko_api.get_menu(venue_id)
    images_map = {}

    def process_category(category):
        for product in category['products']:
            images_map[product['productId']] = product['images']
        for subcategory in category['children']:
            process_category(subcategory)
    for c in menu:
        process_category(c)

    return images_map


class OrderListHandler(BaseHandler):
    @staticmethod
    def today():
        return datetime.datetime.combine(datetime.date.today(), datetime.time())

    def _get_orders(self, venue_id):
        raise NotImplementedError()

    def get(self):
        venue_id = self.request.get('venue_id')
        orders = self._get_orders(venue_id)
        images_map = _build_images_map(venue_id)
        self.render_json({
            'orders': [order.admin_dict(images_map) for order in orders],
            'timestamp': int(time.time())
        })


class CurrentOrdersHandler(OrderListHandler):
    def _get_orders(self, venue_id):
        return Order.query(Order.status.IN([Order.NOT_APPROVED, Order.APPROVED]),
                           Order.venue_id == venue_id,
                           Order.date >= self.today()).fetch()


class OrderUpdatesHandler(OrderListHandler):
    def _get_orders(self, venue_id):
        timestamp = self.request.get_range('timestamp')
        return Order.query(Order.venue_id == venue_id,
                           Order.updated >= datetime.datetime.fromtimestamp(timestamp)).fetch()


class CancelsHandler(OrderListHandler):
    def _get_orders(self, venue_id):
        return Order.query(Order.status == Order.CANCELED,
                           Order.venue_id == venue_id,
                           Order.date >= self.today()).fetch()


class ClosedOrdersHandler(OrderListHandler):
    def _get_orders(self, venue_id):
        return Order.query(Order.status == Order.CLOSED,
                           Order.venue_id == venue_id,
                           Order.date >= self.today()).fetch()

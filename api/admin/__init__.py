# coding=utf-8
import datetime
import time
from ..base import BaseHandler
from methods import iiko_api
from models.iiko import Order


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


class CurrentOrdersHandler(BaseHandler):
    def get(self):
        venue_id = self.request.get('venue_id')
        today = datetime.datetime.combine(datetime.date.today(), datetime.time())
        orders = Order.query(Order.status.IN([Order.NOT_APPROVED, Order.APPROVED]),
                             Order.venue_id == venue_id,
                             Order.date >= today).fetch()

        images_map = _build_images_map(venue_id)
        self.render_json({
            'orders': [order.admin_dict(images_map) for order in orders],
            'timestamp': int(time.time())
        })


class OrderUpdatesHandler(BaseHandler):
    def get(self):
        venue_id = self.request.get('venue_id')
        timestamp = self.request.get_range('timestamp')
        orders = Order.query(Order.status.IN([Order.NOT_APPROVED, Order.APPROVED]),
                             Order.venue_id == venue_id,
                             Order.updated >= datetime.datetime.fromtimestamp(timestamp)).fetch()

        images_map = _build_images_map(venue_id)
        self.render_json({
            'orders': [order.admin_dict(images_map) for order in orders],
            'timestamp': int(time.time())
        })

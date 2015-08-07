# coding=utf-8
import datetime
import time
from ..base import BaseHandler
from methods.iiko.menu import get_menu
from models.admin import Admin
from models.iiko import Order, Customer
from auth import LoginHandler, LogoutHandler
from menu import MenuHandler, DynamicInfoHandler
from stop_list import ItemStopListHandler


def _build_images_map(org_id):
    menu = get_menu(org_id)
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

    def _get_orders(self, delivery_terminal_id):
        raise NotImplementedError()

    def get(self):
        token = self.request.get("token")
        admin = Admin.query(Admin.token == token).get()
        if not admin:
            self.abort(401)

        orders = self._get_orders(admin.delivery_terminal_id)
        images_map = _build_images_map(admin.company_id)
        self.render_json({
            'orders': [order.admin_dict(images_map) for order in orders],
            'timestamp': int(time.time())
        })


class CurrentOrdersHandler(OrderListHandler):
    def _get_orders(self, delivery_terminal_id):
        return Order.query(Order.status.IN([Order.NOT_APPROVED, Order.APPROVED]),
                           Order.delivery_terminal_id == delivery_terminal_id,
                           Order.date >= self.today()).fetch()


class OrderUpdatesHandler(OrderListHandler):
    def _get_orders(self, delivery_terminal_id):
        timestamp = self.request.get_range('timestamp')
        return Order.query(Order.delivery_terminal_id == delivery_terminal_id,
                           Order.updated >= datetime.datetime.fromtimestamp(timestamp)).fetch()


class CancelsHandler(OrderListHandler):
    def _get_orders(self, delivery_terminal_id):
        return Order.query(Order.status == Order.CANCELED,
                           Order.delivery_terminal_id == delivery_terminal_id,
                           Order.date >= self.today()).fetch()


class ClosedOrdersHandler(OrderListHandler):
    def _get_orders(self, delivery_terminal_id):
        return Order.query(Order.status == Order.CLOSED,
                           Order.delivery_terminal_id == delivery_terminal_id,
                           Order.date >= self.today()).fetch()


class ClientHistoryHandler(OrderListHandler):
    def _get_orders(self, delivery_terminal_id):
        customer_id = self.request.get("customer_id")
        customer = Customer.customer_by_customer_id(customer_id)
        if not customer:
            return []
        return Order.query(Order.customer == customer.key).fetch()

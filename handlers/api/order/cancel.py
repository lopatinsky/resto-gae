# coding=utf-8
from handlers.api.base import BaseHandler
from models.iiko import Order

__author__ = 'dvpermyakov'


class CancelOrderHandler(BaseHandler):
    def post(self, order_id):
        order = Order.order_by_id(order_id)
        if order.status in (Order.NOT_APPROVED, Order.APPROVED):
            order.cancel_requested = True
            order.put()
            self.render_json({})
        else:
            self.response.set_status(400)
            self.render_json({'error': u"Заказ уже выдан или отменен"})
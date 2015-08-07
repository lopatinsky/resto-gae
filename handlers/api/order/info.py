from handlers.api.base import BaseHandler
from models import iiko

__author__ = 'dvpermyakov'


class OrderInfoHandler(BaseHandler):
    def get(self, order_id):
        order = iiko.Order.order_by_id(order_id)
        order.reload()

        self.render_json({
            'order': order.to_dict()
        })

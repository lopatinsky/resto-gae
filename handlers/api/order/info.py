from handlers.api.base import BaseHandler
from models import iiko

__author__ = 'dvpermyakov'


class OrderInfoHandler(BaseHandler):
    def get(self, order_id):
        try:
            order = iiko.Order.get_by_id(int(order_id))
        except ValueError:
            order = iiko.Order.order_by_id(order_id)
        if not order:
            self.response.set_status(404)
            return self.render_json({'order': None})
        order.reload()

        self.render_json({
            'order': order.to_dict()
        })

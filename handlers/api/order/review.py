from handlers.api.base import BaseHandler
from models.iiko import Order
from models.iiko.order import OrderRate

__author__ = 'dvpermyakov'


class OrderReviewHandler(BaseHandler):
    def post(self, order_id):
        order = Order.order_by_id(order_id)
        meal_rate = float(self.request.get('meal_rate'))
        service_rate = float(self.request.get('service_rate'))
        comment = self.request.get('comment')
        rate = OrderRate(meal_rate=meal_rate, service_rate=service_rate, comment=comment)
        order.rate = rate
        order.put()
        self.render_json({})


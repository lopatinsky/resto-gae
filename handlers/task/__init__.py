from webapp2 import RequestHandler
from methods.parse_com import send_order_review_push
from models.iiko import Order

__author__ = 'dvpermyakov'

from shared_bonus import SharedBonusActivateHandler


class PushReviewHandler(RequestHandler):
    def post(self):
        order_id = self.request.get('order_id')
        order = Order.order_by_id(order_id)
        send_order_review_push(order)

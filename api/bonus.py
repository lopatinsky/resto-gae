# coding=utf-8

from .base import BaseHandler
from methods.iiko_api import get_orders_with_payments


class GetOrdersWithBonusesHandler(BaseHandler):

    """ /api/get_orders_with_bonuses """

    def get(self):
        venue_id = self.request.get('venue_id')

        self.render_json({"orders": get_orders_with_payments(venue_id)})

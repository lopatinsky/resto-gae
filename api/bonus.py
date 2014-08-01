from api import BaseHandler
from iiko import get_orders_with_payments

__author__ = 'mihailnikolaev'


class GetOrdersWithBonuses(BaseHandler):

    """ /api/get_orders_with_bonuses """

    def get(self):
        date = self.request.get('from')
        venue_id = self.request.get('venue_id')

        self.render_json({"orders": get_orders_with_payments(venue_id)})
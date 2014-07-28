from api.base import BaseHandler
from iiko import get_payment_types

__author__ = 'mihailnikolaev'


class GetPaymentType(BaseHandler):

    """ /api/payment_type/<venue_id> """

    def get(self, venue_id):
        print venue_id
        return self.render_json({"types": get_payment_types(venue_id)})
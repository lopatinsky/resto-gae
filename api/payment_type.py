from api.base import BaseHandler
from models.iiko import Venue


class GetPaymentType(BaseHandler):

    """ /api/payment_type/<venue_id> """

    def get(self, venue_id):
        print venue_id
        return self.render_json({"types": Venue.get_payment_types(venue_id)})

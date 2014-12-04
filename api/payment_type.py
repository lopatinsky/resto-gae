# coding=utf-8

from api.base import BaseHandler
from models.iiko import Venue


class GetPaymentTypesHandler(BaseHandler):

    """ /api/payment_type/<venue_id> """

    def get(self, venue_id):
        return self.render_json({"types": Venue.get_payment_types(venue_id)})

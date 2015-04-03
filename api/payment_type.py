# coding=utf-8

from api.base import BaseHandler
from models.iiko import CompanyNew


class GetPaymentTypesHandler(BaseHandler):

    """ /api/payment_type/<venue_id> """

    def get(self, venue_id):
        return self.render_json({"types": CompanyNew.get_payment_types(venue_id)})

# coding=utf-8

from api.base import BaseHandler
from methods.iiko_api import get_delivery_restrictions


class GetDeliveryRestrictionsHandler(BaseHandler):
    def get(self):
        venue_id = self.request.get('venue_id')

        self.render_json({"restrictions": get_delivery_restrictions(venue_id)})

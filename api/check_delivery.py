import json
from api.base import BaseHandler
from iiko import get_delivery_restrictions, order_info1

__author__ = 'mihailnikolaev'


class GetDeliveryRestrictionsRequestHandler(BaseHandler):
    def get(self):
        venue_id = self.request.get('venue_id')

        self.render_json({"restrictions": get_delivery_restrictions(venue_id)})

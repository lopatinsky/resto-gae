import json
from api.base import BaseHandler
from iiko import get_delivery_restrictions, order_info1

__author__ = 'mihailnikolaev'


class GetDeliveryRestrictionsRequestHandler(BaseHandler):
    def get(self):
        venue_id = self.request.get('venue_id')

        #self.response.out.write(get_delivery_restrictions(venue_id))

        order_id = self.request.get('order_id')

        order_info = order_info1(order_id, venue_id)

        self.response.out.write(json.dumps(order_info))

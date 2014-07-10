from api.base import BaseHandler
from iiko import get_delivery_restrictions

__author__ = 'mihailnikolaev'


class GetDeliveryRestrictionsRequestHandler(BaseHandler):
    def get(self):
        venue_id = self.request.get('venue_id')

        self.response.out.write(get_delivery_restrictions(venue_id))

from api.base import BaseHandler
from methods.maps import complete_address_input_by_kladr

__author__ = 'mihailnikolaev'


class AddressInputHandler(BaseHandler):

    """ /api/address """

    def get(self):
        address = self.request.get('address')
        city = self.request.get('city')
        street = self.request.get('street')
        if address:
            if ' ' not in address:
                return self.render_json([])
            words = address.split(' ', 1)
            city = words[0]
            street = words[1]
        output_data = complete_address_input_by_kladr(city, street)
        return self.render_json(output_data)
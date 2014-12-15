from api.base import BaseHandler
from methods.maps import complete_address_input_by_kladr_with_address
from methods.maps import complete_address_input_by_kladr_with_city_and_street
import logging

__author__ = 'mihailnikolaev'


class AddressInputHandler(BaseHandler):

    """ /api/address """

    def get(self):

        address = self.request.get('address')
        city = self.request.get('city')
        street = self.request.get('street')
        if address:
            output_data = complete_address_input_by_kladr_with_address(address)
        else:
            output_data = complete_address_input_by_kladr_with_city_and_street(city, street)
        return self.render_json(output_data)
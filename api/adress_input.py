from api.base import BaseHandler
from methods.maps import complete_address_input

__author__ = 'mihailnikolaev'


class AddressInputRequestHandler(BaseHandler):

    """ /api/address """

    def get(self):
        address = self.request.get('address')

        output_data = complete_address_input(address)

        return self.render_json(output_data)
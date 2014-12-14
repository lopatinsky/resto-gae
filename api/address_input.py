# coding=utf-8

from api.base import BaseHandler
from methods.maps import complete_address_input, complete_address_input_by_kladr


class AddressInputHandler(BaseHandler):

    """ /api/address """

    def get(self):
        address = self.request.get('address')

        output_data = complete_address_input_by_kladr(address)
        #output_data = complete_address_input(address)

        return self.render_json(output_data)

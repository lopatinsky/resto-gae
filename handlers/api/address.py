import logging
from handlers.api.base import BaseHandler
from methods.iiko.address import complete_address_input_by_iiko
from methods.maps import complete_address_input_by_kladr
from models.iiko.company import CompanyNew

__author__ = 'mihailnikolaev'


class AddressByStreetHandler(BaseHandler):
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

        ua = self.request.user_agent
        name = ua.split('/', 1)[0].lower().strip()
        logging.debug('searching for company with name %r', name)
        company = CompanyNew.query(CompanyNew.app_name == name).get()
        logging.debug('result: %s' % company)

        if company:
            logging.debug('searching by iiko')
            output_data = complete_address_input_by_iiko(company, city, street)
        else:
            logging.debug('searching by kladr')
            output_data = complete_address_input_by_kladr(city, street)
        return self.render_json(output_data)

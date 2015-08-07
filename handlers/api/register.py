import json
import logging
from methods import filter_phone
from methods.iiko.customer import get_customer_by_phone, create_or_update_customer
from models.iiko import CompanyNew, Customer
from models.specials import Share, SharedBonus
from base import BaseHandler

__author__ = 'dvpermyakov'


class RegisterHandler(BaseHandler):
    def post(self):
        company_id = self.request.get_range('company_id')
        company = CompanyNew.get_by_id(company_id)
        requested_customer_id = customer_id = self.request.get('customer_id')
        phone = filter_phone(self.request.get('phone'))
        if not customer_id:
            iiko_customer = get_customer_by_phone(company, phone)
            customer_id = iiko_customer.get('id')
            if not customer_id:
                iiko_customer = {'phone': phone, 'balance': 0}
                customer_id = create_or_update_customer(company, iiko_customer)
                customer = Customer(phone=phone, customer_id=customer_id)
                customer.put()
            else:
                customer = Customer.customer_by_customer_id(customer_id)
                if not customer:
                    customer = Customer(phone=phone, customer_id=customer_id)
                    customer.put()
        else:
            customer = Customer.customer_by_customer_id(customer_id)
            if not customer:
                customer = Customer(phone=phone, customer_id=customer_id)
                customer.put()
        share_data = self.request.get('share_data')
        if share_data:
            share_data = json.loads(share_data)
            share_id = share_data.get('share_id')
            share = None
            if share_id:
                share = Share.get_by_id(share_id)
            if share:
                logging.info('share has')
                if share.share_type == Share.INVITATION:
                    logging.info('invitaion has')
                    if not requested_customer_id:
                        logging.info('customer has not')
                        SharedBonus(sender=share.sender, recipient=customer.key, share_id=share.key.id()).put()
        self.render_json({
            'customer_id': customer_id
        })
import json
from methods.branch_io import INVITATION
from methods.customer import get_resto_customer
from models.iiko import CompanyNew
from models.specials import Share, SharedBonus
from base import BaseHandler

__author__ = 'dvpermyakov'


class RegisterHandler(BaseHandler):
    def post(self):
        company_id = self.request.get_range('company_id')
        company = CompanyNew.get_by_id(company_id)
        customer_id = self.request.get('customer_id')
        customer = get_resto_customer(company, customer_id)
        share_data = self.request.get('share_data')
        if share_data:
            share_data = json.loads(share_data)
            share_id = share_data.get('share_id', 0)
            share = Share.get_by_id(share_id)
            if share:
                if share.share_type == INVITATION and not customer_id:
                    SharedBonus(sender=share.sender, recipient=customer.key, share_id=share.key.id()).put()
        self.render_json({
            'customer_id': customer_id
        })

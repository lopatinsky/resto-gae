# coding=utf-8

from api.base import BaseHandler
from models.iiko import CompanyNew, DeliveryTerminal


class GetPaymentTypesHandler(BaseHandler):

    """ /api/payment_type/<venue_id> """

    def get(self, delivery_terminal_id):
        delivery_terminal = DeliveryTerminal.get_by_id(delivery_terminal_id)
        if delivery_terminal:
            iiko_org_id = delivery_terminal.iiko_organization_id
        else:
            iiko_org_id = delivery_terminal_id
        return self.render_json({"types": CompanyNew.get_payment_types(iiko_org_id)})


class CompanyPaymentTypesHandler(BaseHandler):
    def get(self, company_id):
        company = CompanyNew.get_by_id(int(company_id))
        self.render_json({
            "types": [pt.get().to_dict() for pt in company.payment_types]
        })

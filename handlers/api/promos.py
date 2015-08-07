# coding=utf-8
from .base import BaseHandler
from methods.iiko.customer import get_customer_by_phone
from methods.iiko.promo import get_venue_promos
from methods import filter_phone
from models.iiko import CompanyNew, DeliveryTerminal

CAT_FREE_CUP_CODES = {
    CompanyNew.EMPATIKA: ['3308081521040829', '3308081521040830'],
    CompanyNew.COFFEE_CITY: ['0264', '0265', '0266', '0267', '0268', '0269', '0272'],
}
CUPS_BEFORE_FREE_CUP = 5


def _do_get_promos(company, phone):
    return {
        "promos": get_venue_promos(company.iiko_org_id),
        "balance": get_customer_by_phone(company, phone).get('balance', 0.0)
    }


class CompanyPromosHandler(BaseHandler):
    def get(self, company_id):
        company = CompanyNew.get_by_id(int(company_id))
        phone = filter_phone(self.request.get('phone'))
        self.render_json(_do_get_promos(company, phone))


class VenuePromosHandler(BaseHandler):
    def get(self):
        delivery_terminal_id = self.request.get('venue_id')
        delivery_terminal = DeliveryTerminal.get_by_id(delivery_terminal_id)
        if delivery_terminal:
            org_id = delivery_terminal.iiko_organization_id
        else:
            org_id = delivery_terminal_id
        company = CompanyNew.get_by_iiko_id(org_id)
        phone = filter_phone(self.request.get('phone'))

        self.render_json(_do_get_promos(company, phone))

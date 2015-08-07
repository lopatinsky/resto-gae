# coding=utf-8
from handlers.api.base import BaseHandler
from methods.iiko.menu import get_menu
from methods.specials.cat import fix_syrop, fix_modifiers_by_own
from models.iiko import CompanyNew, DeliveryTerminal

__author__ = 'dvpermyakov'


class CompanyDeliveryTypesHandler(BaseHandler):
    def get(self):
        company_id = self.request.get('organization_id')
        return self.render_json({
            "types": CompanyNew.get_delivery_types(company_id)
        })


class CompanyPaymentTypesHandler(BaseHandler):
    def get(self, company_id):
        company = CompanyNew.get_by_id(int(company_id))
        self.render_json({
            "types": [payment_type.get().to_dict() for payment_type in company.payment_types]
        })


class CompanyMenuHandler(BaseHandler):
    def get(self, company_id):
        iiko_org_id = CompanyNew.get_by_id(int(company_id)).iiko_org_id
        force_reload = "reload" in self.request.params
        filtered = "all" not in self.request.params
        menu = get_menu(iiko_org_id, force_reload=force_reload, filtered=filtered)
        if iiko_org_id == CompanyNew.COFFEE_CITY:
            menu = fix_syrop.set_syrop_modifiers(menu)
            menu = fix_modifiers_by_own.remove_modifiers(menu)
        self.render_json({'menu': menu})


class CompanyVenuesHandler(BaseHandler):
    def get(self, company_id):
        company = CompanyNew.get_by_id(int(company_id))
        venues = DeliveryTerminal.query(DeliveryTerminal.company_id == company.key.id(),
                                        DeliveryTerminal.active == True).fetch()
        self.render_json({
            'venues': [venue.to_dict() for venue in venues]
        })

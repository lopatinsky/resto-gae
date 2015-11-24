# coding=utf-8
from handlers.api.base import BaseHandler
from methods.customer import get_resto_customer
from methods.iiko.menu import get_menu, add_additional_categories, get_company_stop_lists
from methods.specials.cat import fix_syrop, fix_modifiers_by_own
from models.iiko import CompanyNew, DeliveryTerminal, Order

__author__ = 'dvpermyakov'


class CompanyInfoHandler(BaseHandler):
    def get(self):
        company_id = self.request.get_range('company_id')
        company = CompanyNew.get_by_id(company_id)
        client_id = self.request.get('client_id')
        customer = get_resto_customer(company, client_id)
        branch_invitation = company.invitation_settings is not None and company.invitation_settings.enable
        if branch_invitation and 'orangexpress/1.2.2' in self.request.user_agent:
            branch_invitation = Order.query(Order.customer == customer.key).get() is not None
        self.render_json({
            'app_name': company.app_title,
            'description': company.description,
            'min_order_sum': company.min_order_sum,
            'cities': company.cities,
            'phone': company.phone,
            'schedule': company.schedule,
            'email': company.email,
            'support_emails': company.support_emails,
            'site': company.site,
            'branch_invitation': branch_invitation,
            'branch_gift': company.branch_gift_enable
        })


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
        company = CompanyNew.get_by_id(int(company_id))
        force_reload = "reload" in self.request.params
        filtered = "all" not in self.request.params
        menu = get_menu(company.iiko_org_id, force_reload=force_reload, filtered=filtered)
        if company.iiko_org_id == CompanyNew.COFFEE_CITY:
            menu = fix_syrop.set_syrop_modifiers(menu)
            menu = fix_modifiers_by_own.remove_modifiers(menu)
        add_additional_categories(company, menu)
        self.render_json({'menu': menu})


class CompanyVenuesHandler(BaseHandler):
    def get(self, company_id):
        company = CompanyNew.get_by_id(int(company_id))
        venues = DeliveryTerminal.query(DeliveryTerminal.company_id == company.key.id(),
                                        DeliveryTerminal.active == True).fetch()
        self.render_json({
            'venues': [venue.to_dict() for venue in venues]
        })


class RemaindersHandler(BaseHandler):
    def get(self, company_id):
        company = CompanyNew.get_by_id(int(company_id))
        stop_lists = get_company_stop_lists(company)
        venues = DeliveryTerminal.query(DeliveryTerminal.company_id == company.key.id(),
                                        DeliveryTerminal.active == True).fetch()
        item_id = self.request.get("item_id")

        result = {}
        for venue in venues:
            if venue.key.id() not in stop_lists or \
                    item_id not in stop_lists[venue.key.id()]:
                remainders = None
            else:
                remainders = stop_lists[venue.key.id()][item_id]
                if remainders < 0:
                    remainders = 0
            result[venue.key.id()] = remainders
        self.render_json({
            'item_id': item_id,
            'remainders': result
        })

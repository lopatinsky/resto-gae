from handlers.api.base import BaseHandler
from methods.iiko.menu import get_menu
from methods.specials.cat import fix_syrop, fix_modifiers_by_own
from models.iiko import CompanyNew, DeliveryTerminal

__author__ = 'dvpermyakov'


class VenuePaymentTypesHandler(BaseHandler):
    def get(self, delivery_terminal_id):
        delivery_terminal = DeliveryTerminal.get_by_id(delivery_terminal_id)
        if delivery_terminal:
            iiko_org_id = delivery_terminal.iiko_organization_id
        else:
            iiko_org_id = delivery_terminal_id
        return self.render_json({"types": CompanyNew.get_payment_types(iiko_org_id)})


class VenueMenuHandler(BaseHandler):
    def get(self, delivery_terminal_id):
        delivery_terminal = DeliveryTerminal.get_by_id(delivery_terminal_id)
        if delivery_terminal:
            iiko_org_id = delivery_terminal.iiko_organization_id
        else:
            iiko_org_id = delivery_terminal_id
        force_reload = "reload" in self.request.params
        filtered = "all" not in self.request.params
        menu = get_menu(iiko_org_id, force_reload=force_reload, filtered=filtered)
        if iiko_org_id == CompanyNew.COFFEE_CITY:
            menu = fix_syrop.set_syrop_modifiers(menu)
            menu = fix_modifiers_by_own.remove_modifiers(menu)
        self.render_json({'menu': menu})
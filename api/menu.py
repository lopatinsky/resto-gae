# coding=utf-8

from api.base import BaseHandler
from methods import iiko_api
from models.iiko import CompanyNew, DeliveryTerminal
from specials import fix_syrop, fix_modifiers_by_own


class MenuHandler(BaseHandler):
    """ /api/venue/%s/menu """
    def get(self, venue_id):
        iiko_org_id = DeliveryTerminal.get_by_id(venue_id).iiko_organization_id
        force_reload = "reload" in self.request.params
        filtered = "all" not in self.request.params
        menu = iiko_api.get_menu(iiko_org_id, force_reload=force_reload, filtered=filtered)
        if iiko_org_id == CompanyNew.COFFEE_CITY:
            menu = fix_syrop.set_syrop_modifiers(menu)
            menu = fix_modifiers_by_own.remove_modifiers(menu)
        self.render_json({'menu': menu})

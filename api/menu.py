# coding=utf-8

from api.base import BaseHandler
from methods import iiko_api
from specials import fix_syrop, fix_modifiers_by_own


class MenuHandler(BaseHandler):
    """ /api/venue/%s/menu """
    def get(self, venue_id):
        force_reload = "reload" in self.request.params
        filtered = "all" not in self.request.params
        menu = iiko_api.get_menu(venue_id, force_reload=force_reload, filtered=filtered)
        if venue_id == fix_syrop.COFFE_AND_THE_CITY_ID:
            menu = fix_syrop.set_syrop_modifiers(menu)
            menu = fix_modifiers_by_own.remove_modifiers(menu)
        self.render_json({'menu': menu})

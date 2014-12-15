# coding=utf-8

from api.base import BaseHandler
from methods import iiko_api


class MenuHandler(BaseHandler):
    """ /api/venue/%s/menu """
    def get(self, venue_id):
        force_reload = "reload" in self.request.params
        filtered = "all" not in self.request.params
        menu = iiko_api.get_menu(venue_id, force_reload=force_reload, filtered=filtered)
        self.render_json({'menu': menu})

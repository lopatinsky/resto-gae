from api.base import BaseHandler
from methods import iiko_api

__author__ = 'quiker'


class MenuRequestHandler(BaseHandler):
    """ /api/venue/%s/menu """
    def get(self, venue_id):
        menu = iiko_api.get_menu(venue_id)
        self.render_json({'menu': menu})

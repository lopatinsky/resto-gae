import json
import webapp2
from api.base import BaseHandler
import iiko

__author__ = 'quiker'


class MenuRequestHandler(BaseHandler):
    """ /api/venue/%s/menu """
    def get(self, venue_id):
        menu = iiko.get_menu(venue_id)
        self.render_json({'menu': menu})
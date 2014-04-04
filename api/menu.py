import json
import webapp2
import iiko

__author__ = 'quiker'


class MenuRequestHandler(webapp2.RequestHandler):
    """ /api/venue/%s/menu """
    def get(self, venue_id):
        menu = iiko.get_menu(venue_id)

        self.response.headers['Content-Type'] = 'application/json'
        self.response.out.write(json.dumps({
            'menu': menu
        }))
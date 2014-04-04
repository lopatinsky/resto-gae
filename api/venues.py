import json
import webapp2
import iiko

__author__ = 'quiker'


class VenuesHandler(webapp2.RequestHandler):
    """ /api/venues """
    def get(self):
        venues = iiko.get_venues()

        self.response.headers['Content-Type'] = 'application/json'
        self.response.out.write(json.dumps({
            'venues': [venue.to_dict() for venue in venues]
        }))
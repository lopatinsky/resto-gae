import logging
from google.appengine.api import memcache
import webapp2
from methods import iiko_api
from models.iiko import Venue


class UpdateMenuHandler(webapp2.RequestHandler):
    def get(self):
        venues = Venue.query().fetch()
        for venue in venues:
            try:
                iiko_api.load_menu(venue)
                memcache.set('iiko_menu_%s' % venue.venue_id, venue.menu, time=1*3600)
            except Exception as e:
                logging.exception(e)

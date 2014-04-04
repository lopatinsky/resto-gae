from google.appengine.ext import ndb
from google.appengine.api import memcache
from lib import geocoding

__author__ = 'quiker'


class Venue(ndb.Model):
    venue_id = ndb.StringProperty()
    name = ndb.StringProperty()
    logo_url = ndb.StringProperty(indexed=False)
    address = ndb.StringProperty(indexed=False)
    phone = ndb.StringProperty(indexed=False)
    latitude = ndb.FloatProperty(indexed=False)
    longitude = ndb.FloatProperty(indexed=False)
    source = ndb.StringProperty()

    @classmethod
    def venue_by_id(cls, venue_id):
        venue = memcache.get('venue_%s' % venue_id)
        if venue is None:
            venue = cls.query(cls.venue_id == venue_id).get()
        return venue

    @classmethod
    def venue_with_dict(cls, dict_venue):
        venue = cls.venue_by_id(dict_venue['id'])
        should_put = False
        if not venue:
            should_put = True
            venue = Venue()
            venue.venue_id = dict_venue['id']
            venue.name = dict_venue['name']
            venue.source = 'iiko'
        venue.logo_url = dict_venue['logo']
        venue.phone = dict_venue['contact'].get('phone')
        address = dict_venue['contact']['location']
        if venue.address != address:
            should_put = True
            venue.address = address
            venue.latitude, venue.longitude = geocoding.get_address_coordinates(address)
        if should_put:
            venue.put()
            memcache.set('venue_%s' % venue.venue_id, venue, time=30*60)
        return venue

    def to_dict(self):
        return {
            'venueId': self.venue_id,
            'name': self.name,
            'address': self.address,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'logoUrl': self.logo_url,
            'phone': self.phone
        }
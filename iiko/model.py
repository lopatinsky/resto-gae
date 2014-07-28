# coding=utf-8
from google.appengine.ext import ndb
from google.appengine.api import memcache
from lib import geocoding

__author__ = 'quiker'


class Customer(ndb.Model):
    phone = ndb.StringProperty()
    name = ndb.StringProperty(indexed=False)
    customer_id = ndb.StringProperty()

    @classmethod
    def customer_by_phone(cls, phone):
        return cls.query(cls.phone == phone).get()

    @classmethod
    def customer_by_customer_id(cls, customer_id):
        return cls.query(cls.customer_id == customer_id).get()


class Order(ndb.Model):
    # statuses
    UNKNOWN = -1
    NOT_APPROVED = 1
    APPROVED = 2
    CLOSED = 3
    CANCELED = 4

    date = ndb.DateTimeProperty()
    sum = ndb.FloatProperty(indexed=False)
    items = ndb.JsonProperty()
    is_delivery = ndb.BooleanProperty(default=False)
    address = ndb.JsonProperty()
    venue_id = ndb.StringProperty()
    customer = ndb.KeyProperty()
    order_id = ndb.StringProperty()
    number = ndb.StringProperty()
    status = ndb.IntegerProperty()

    def set_status(self, status):
        if status.find(u'Не подтверждена') >= 0:
            self.status = self.NOT_APPROVED
        elif status.find(u'Новая') >= 0:
            self.status = self.APPROVED
        elif status.find(u'Закрыта') >= 0:
            self.status = self.CLOSED
        elif status.find(u'Отменена') >= 0:
            self.status = self.CANCELED
        else:
            self.status = self.UNKNOWN

    @classmethod
    def order_by_id(cls, order_id):
        return cls.query(cls.order_id == order_id).get()

    def to_dict(self):
        serialized =  {
            'orderId': self.order_id,
            'number': self.number,
            'status': self.status,
            'sum': self.sum,
            'items': self.items,
            'venueId': self.venue_id
        }

        return serialized


class Venue(ndb.Model):
    venue_id = ndb.StringProperty()
    name = ndb.StringProperty()
    logo_url = ndb.StringProperty(indexed=False)
    address = ndb.StringProperty(indexed=False)
    phone = ndb.StringProperty(indexed=False)
    latitude = ndb.FloatProperty(indexed=False)
    longitude = ndb.FloatProperty(indexed=False)
    source = ndb.StringProperty()
    company_id = ndb.IntegerProperty()

    @classmethod
    def venue_by_id(cls, venue_id):
        venue = memcache.get('venue_%s' % venue_id)
        if venue is None:
            venue = cls.query(cls.venue_id == venue_id).get()
        return venue

    @classmethod
    def venue_with_dict(cls, dict_venue, org_id):
        venue = cls.venue_by_id(dict_venue['id'])
        should_put = False
        if not venue:
            should_put = True
            venue = Venue()
            venue.venue_id = dict_venue['id']
            venue.name = dict_venue['name']
            venue.source = 'iiko'
            venue.company_id = org_id
        venue.logo_url = dict_venue['logo']
        venue.phone = dict_venue['contact'].get('phone')
        address = dict_venue['contact']['location']
        if venue.address != address:
            should_put = True
            venue.address = address
            venue.latitude, venue.longitude = geocoding.get_address_coordinates(address)
        if not venue.company_id:
            should_put = True
            venue.company_id = org_id
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


class Company(ndb.Model):
    name = ndb.StringProperty()
    password = ndb.StringProperty()

    def get_id(self):
        return self.key.id()
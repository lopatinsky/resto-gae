# coding=utf-8
from google.appengine.ext import ndb
from google.appengine.api import memcache
from methods import maps


__author__ = 'quiker'


class PaymentType(ndb.Model):
    name = ndb.StringProperty()
    type_id = ndb.IntegerProperty()
    iiko_uuid = ndb.StringProperty()
    available = ndb.BooleanProperty()

    def to_dict(self):
        return {
            'type_id': self.type_id,
            'name': self.name,
            'iiko_uuid': self.iiko_uuid,
            'available': self.available
        }

    @classmethod
    def check_existence(cls, type_id, iiko_uuid):
        for typ in PaymentType.query():
            if typ.type_id == int(type_id) and typ.iiko_uuid == iiko_uuid:
                return typ
        return None

    @classmethod
    def get_by_type_id(cls, type_id):
        return PaymentType.query().filter(PaymentType.type_id == int(type_id)).get()


class DeliveryType(ndb.Model):
    delivery_id = ndb.IntegerProperty()
    name = ndb.StringProperty()
    available = ndb.BooleanProperty()

    def to_dict(self):
        return {
            'type_id': self.delivery_id,
            'name': self.name,
            'available': self.available
        }

    @classmethod
    def check_existence(cls, delivery_id):
        for typ in DeliveryType.query():
            if typ.delivery_id == int(delivery_id):
                return typ
        return None


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
    comment = ndb.StringProperty()
    payment_type = ndb.StringProperty()
    alfa_order_id = ndb.StringProperty()


    # TODO Need to check english statuses(may be incorrect)
    @classmethod
    def parse_status(cls, status):
        status = status.lower()
        if u'не подтверждена' in status or 'waiting for confirmation':
            return cls.NOT_APPROVED
        elif u'новая' in status or 'new' in status or u'ждет отправки' in status\
                or u'в пути' in status or u'готовится' in status or u'готово' in status:
            return cls.APPROVED
        elif u'закрыта' in status or 'closed' in status or u'доставлена' in status:
            return cls.CLOSED
        elif u'отменена' in status or 'cancelled' in status:
            return cls.CANCELED
        else:
            return cls.UNKNOWN

    def set_status(self, status):
        self.status = self.parse_status(status)

    @classmethod
    def order_by_id(cls, order_id):
        return cls.query(cls.order_id == order_id).get()

    def to_dict(self):
        serialized = {
            'orderId': self.order_id,
            'number': self.number,
            'status': self.status,
            'sum': self.sum,
            'items': self.items,
            'venueId': self.venue_id,
            'address': self.address
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
    payment_types = ndb.KeyProperty(kind=PaymentType, repeated=True)

    @classmethod
    def get_payment_types(cls, venue_id):
        venue = cls.venue_by_id(venue_id)
        output = []
        for item in ndb.get_multi(venue.payment_types):
            output.append(item.to_dict())
        return output

    def check_ext(self, type_id):
        for item in ndb.get_multi(self.payment_types):
            if item.type_id == int(type_id):
                return True
        return False

    @classmethod
    def venue_by_id(cls, venue_id):
        venue = memcache.get('venue_%s' % venue_id)
        if venue is None:
            venue = cls.query(cls.venue_id == venue_id).get()
            memcache.set('venue_%s' % venue_id, venue, time=30*60)
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
            venue.latitude, venue.longitude = maps.get_address_coordinates(address)
        if not venue.company_id:
            should_put = True
            venue.company_id = org_id
        if should_put:
            venue.put()
            memcache.set('venue_%s' % venue.venue_id, venue, time=30*60)
        return venue

    def get_timezone_offset(self):
        result = memcache.get('venue_%s_timezone' % self.venue_id)
        if not result:
            result = maps.get_timezone_by_coords(self.latitude, self.longitude)
            memcache.set('venue_%s_timezone' % self.venue_id, result, time=24*3600)
        return result

    def to_dict(self):
        return {
            'venueId': self.venue_id,
            'name': self.name,
            'address': self.address,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'logoUrl': self.logo_url,
            'phone': self.phone,
            'payment_types': [x.to_dict() for x in ndb.get_multi(self.payment_types)]
        }


class Company(ndb.Model):
    name = ndb.StringProperty()
    password = ndb.StringProperty()
    delivery_types = ndb.KeyProperty(kind=DeliveryType, repeated=True)

    def get_id(self):
        return self.key.id()

    def check_ext(self, delivery_id):
        for item in ndb.get_multi(self.delivery_types):
            if item.delivery_id == int(delivery_id):
                return True
        return False

    @classmethod
    def get_delivery_types(cls, org_id):
        org = cls.get_by_id(int(org_id))
        output = []
        for item in ndb.get_multi(org.delivery_types):
            output.append(item.to_dict())
        return output


class ImageCache(ndb.Model):
    # key name is urlsafe_b64encoded image URL
    updated = ndb.DateTimeProperty(auto_now=True)
    last_modified = ndb.StringProperty(indexed=False)
    serving_url = ndb.StringProperty(indexed=False)

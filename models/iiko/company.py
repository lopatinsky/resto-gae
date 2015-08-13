# coding=utf-8
from google.appengine.api import memcache
from google.appengine.ext import ndb

__author__ = 'dvpermyakov'


class PaymentType(ndb.Model):
    CASH = '1'
    CARD = '2'
    COURIER_CARD = '3'

    PAYMENT_MAP = {
        CASH: u'Наличные',
        CARD: u'Карта',
        COURIER_CARD: u'Карта курьеру'
    }

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


class IikoApiLogin(ndb.Model):
    @property
    def login(self):
        return self.key.id()

    password = ndb.StringProperty(indexed=False)


class CompanyNew(ndb.Model):
    COFFEE_CITY = "02b1b1f7-4ec8-11e4-80cc-0025907e32e9"
    EMPATIKA_OLD = "95e4a970-b4ea-11e3-8bac-50465d4d1d14"
    EMPATIKA = "5cae16f4-4039-11e5-80d2-d8d38565926f"
    MIVAKO = "6a05d004-e03d-11e3-bae4-001b21b8a590"
    ORANGE_EXPRESS = "768c213e-5bc1-4135-baa3-45f719dbad7e"
    SUSHILAR = "a9d16dff-7680-43f1-b1a1-74784bc75f60"
    VENEZIA = "b4c224da-b1d2-11e4-80d8-002590dc3769"
    DIMASH = "d3b9ba12-ee62-11e4-80cf-d8d38565926f"
    BON_APPETIT = "610ebd80-ada9-11e3-bae4-001b21b8a590"
    TYKANO = "a637b109-218f-11e5-80c1-d8d385655247"
    BURGER_CLUB = "e7985b2c-a21b-11e4-80d2-0025907e32e9"
    PANDA = "09ac1efb-2578-11e5-80d2-d8d38565926f"
    PIZZA_HUT = "107662a7-39d5-11e5-80c1-d8d385655247"

    iiko_login = ndb.StringProperty()
    iiko_org_id = ndb.StringProperty()

    address = ndb.StringProperty(indexed=False)
    latitude = ndb.FloatProperty(indexed=False)
    longitude = ndb.FloatProperty(indexed=False)

    delivery_types = ndb.KeyProperty(kind=DeliveryType, repeated=True)
    payment_types = ndb.KeyProperty(kind=PaymentType, repeated=True)
    menu = ndb.JsonProperty()

    app_name = ndb.StringProperty(repeated=True)  # TODO REMOVE: part of user-agent to identify app in alfa handler
    app_title = ndb.StringProperty()
    alpha_login = ndb.StringProperty(indexed=False)
    alpha_pass = ndb.StringProperty(indexed=False)
    card_button_text = ndb.StringProperty()
    card_button_subtext = ndb.StringProperty()

    is_iiko_system = ndb.BooleanProperty(default=False)
    new_endpoints = ndb.BooleanProperty(default=False)

    branch_invitation_enable = ndb.BooleanProperty(default=False)
    branch_gift_enable = ndb.BooleanProperty(default=False)
    rbcn_mobi = ndb.StringProperty(indexed=False)

    review_enable = ndb.BooleanProperty(default=False)

    description = ndb.StringProperty()
    min_order_sum = ndb.IntegerProperty()
    email = ndb.StringProperty()
    support_emails = ndb.StringProperty(repeated=True)
    site = ndb.StringProperty()
    cities = ndb.StringProperty(repeated=True)
    phone = ndb.StringProperty()
    schedule = ndb.JsonProperty()
    icon1 = ndb.BlobProperty()
    icon2 = ndb.BlobProperty()
    icon3 = ndb.BlobProperty()
    icon4 = ndb.BlobProperty()
    company_icon = ndb.BlobProperty()
    color = ndb.StringProperty()
    analytics_key = ndb.StringProperty()

    ios_push_channel = ndb.StringProperty()
    android_push_channel = ndb.StringProperty()

    @classmethod
    def get_payment_types(cls, venue_id):
        venue = cls.get_by_iiko_id(venue_id)
        output = []
        for item in ndb.get_multi(venue.payment_types):
            output.append(item.to_dict())
        return output

    def get_payment_type(self, type_id):
        if type_id:
            for item in ndb.get_multi(self.payment_types):
                if item.type_id == int(type_id):
                    return item
        return None

    @classmethod
    def get_delivery_types(cls, company_id):
        company = cls.get_by_id(int(company_id))
        output = []
        for item in ndb.get_multi(company.delivery_types):
            output.append(item.to_dict())
        return output

    @classmethod
    def get_by_iiko_id(cls, iiko_org_id):
        return cls.query(cls.iiko_org_id == iiko_org_id).get()

    def get_timezone_offset(self):
        from methods import maps
        result = memcache.get('venue_%s_timezone' % self.iiko_org_id)
        if not result:
            result = maps.get_timezone_by_coords(self.latitude, self.longitude)
            memcache.set('venue_%s_timezone' % self.iiko_org_id, result, time=24*3600)
        return result

from google.appengine.ext import ndb
from google.appengine.ext.ndb import transactional
from webapp2_extras import security
from models.iiko.company import CompanyNew

__author__ = 'dvpermyakov'

IOS_DEVICE = 0
ANDROID_DEVICE = 1


class Customer(ndb.Model):
    created = ndb.DateTimeProperty(auto_now_add=True)
    updated = ndb.DateTimeProperty(auto_now=True)
    company = ndb.KeyProperty(kind=CompanyNew)
    customer_id = ndb.StringProperty()                 # it relates to iiko
    phone = ndb.StringProperty()
    name = ndb.StringProperty(indexed=False)
    user_agent = ndb.StringProperty()
    custom_data = ndb.JsonProperty()

    @classmethod
    def generate_customer_id(cls):
        while True:
            key = security.generate_random_string(entropy=256)
            customer = cls.query(cls.customer_id == key).get()
            if not customer:
                customer = cls.get_by_id(key)
            if not customer:
                return key

    @classmethod
    def customer_by_customer_id(cls, customer_id):
        return cls.query(cls.customer_id == customer_id).get()

    @classmethod
    def customer_by_phone(cls, phone):   # todo: it is wrong! search only by customer_id
        return cls.query(cls.phone == phone).get()

    def get_device(self):
        if not self.user_agent:
            return
        if 'Android' in self.user_agent:
            return ANDROID_DEVICE
        elif 'iOS' in self.user_agent:
            return IOS_DEVICE


class BonusCardHack(ndb.Model):
    customer_id = ndb.StringProperty(indexed=False)

    @property
    def phone(self):
        return self.key.id()

    @classmethod
    def get(cls, phone):
        phone_without_plus = phone.lstrip('+')
        entity = cls.get_by_id(phone_without_plus) if phone_without_plus else None
        if entity:
            return phone_without_plus, entity.customer_id
        return phone, None


class ClientInfo(ndb.Model):
    company_id = ndb.IntegerProperty(required=True)
    phone = ndb.StringProperty()
    email = ndb.StringProperty()
    created_at = ndb.DateTimeProperty(auto_now_add=True)
    user_agent = ndb.StringProperty()
    customer = ndb.KeyProperty(Customer)

    def get_device(self):
        if not self.user_agent:
            return
        if 'Android' in self.user_agent:
            return ANDROID_DEVICE
        elif 'iOS' in self.user_agent:
            return IOS_DEVICE

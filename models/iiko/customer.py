from google.appengine.ext import ndb

__author__ = 'dvpermyakov'


class AvailableConfirmation(ndb.Model):
    requested_phone = ndb.StringProperty(required=True)
    code = ndb.IntegerProperty(required=True)


class Customer(ndb.Model):
    phone = ndb.StringProperty()
    name = ndb.StringProperty(indexed=False)
    user_agent = ndb.StringProperty()
    customer_id = ndb.StringProperty()
    custom_data = ndb.JsonProperty()

    confirmations = ndb.StructuredProperty(AvailableConfirmation, repeated=True)
    confirmed_phones = ndb.StringProperty(repeated=True)

    @classmethod
    def customer_by_phone(cls, phone):
        return cls.query(cls.phone == phone).get()

    @classmethod
    def customer_by_customer_id(cls, customer_id):
        return cls.query(cls.customer_id == customer_id).get()

    def get_device(self):
        from methods.parse_com import ANDROID_DEVICE, IOS_DEVICE
        if not self.user_agent:
            return
        if 'Android' in self.user_agent:
            return ANDROID_DEVICE
        elif 'iOS' in self.user_agent:
            return IOS_DEVICE


class BonusCardHack(ndb.Model):
    def phone(self):
        return self.key.id()

    customer_id = ndb.StringProperty(indexed=False)

    @classmethod
    def check(cls, phone):
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
        from methods.parse_com import ANDROID_DEVICE, IOS_DEVICE
        if not self.user_agent:
            return
        if 'Android' in self.user_agent:
            return ANDROID_DEVICE
        elif 'iOS' in self.user_agent:
            return IOS_DEVICE

# coding=utf-8

from google.appengine.ext import ndb
from models.iiko import Customer, PaymentType


class MivakoGift(ndb.Model):
    sender = ndb.StringProperty()
    recipient = ndb.StringProperty()
    recipient_name = ndb.StringProperty()
    datetime = ndb.DateTimeProperty(auto_now_add=True)
    emailed = ndb.BooleanProperty(default=False)
    gift_item = ndb.StringProperty()


class Notification(ndb.Model):  # old class for storage pushes
    PUSH_NOTIFICATION = 0

    #order_id = ndb.StringProperty(required=True)  old type of notification
    client_id = ndb.StringProperty(required=True)
    created = ndb.DateTimeProperty(auto_now_add=True)
    type = ndb.IntegerProperty(required=True)


class MassPushHistory(ndb.Model):
    created = ndb.DateTimeProperty(auto_now_add=True)

    text = ndb.StringProperty()
    head = ndb.StringProperty()
    android_avail = ndb.BooleanProperty()
    android_channels = ndb.StringProperty(repeated=True)
    ios_avail = ndb.BooleanProperty()
    ios_channels = ndb.StringProperty(repeated=True)
    company_ids = ndb.IntegerProperty(repeated=True)
    parse_response = ndb.JsonProperty()


class CATSocialId(ndb.Model):
    venue_id = ndb.StringProperty()
    customer_id = ndb.StringProperty()
    provider = ndb.StringProperty()
    social_id = ndb.StringProperty()

    created = ndb.DateTimeProperty(auto_now_add=True)


class Share(ndb.Model):
    from methods.branch_io import SHARE, INVITATION, GIFT

    ACTIVE = 0
    INACTIVE = 1

    sender = ndb.KeyProperty(required=True, kind=Customer)
    share_type = ndb.IntegerProperty(required=True, choices=[SHARE, INVITATION, GIFT])
    created = ndb.DateTimeProperty(auto_now_add=True)
    status = ndb.IntegerProperty(default=ACTIVE)
    urls = ndb.StringProperty(repeated=True)

    def deactivate(self):
        self.status = self.INACTIVE
        self.put()


class SharedBonus(ndb.Model):
    READY = 0
    DONE = 1

    sender = ndb.KeyProperty(required=True, kind=Customer)
    recipient = ndb.KeyProperty(required=True, kind=Customer)
    share_id = ndb.IntegerProperty(required=True)
    created = ndb.DateTimeProperty(auto_now_add=True)
    status = ndb.IntegerProperty(choices=[READY, DONE], default=READY)

    def deactivate(self, company):
        from methods import iiko_api
        iiko_customer = iiko_api.get_customer_by_id(company, self.recipient.get().customer_id)
        iiko_customer['balance'] += 20
        iiko_api.create_or_update_customer(company, iiko_customer)
        self.status = self.DONE
        self.put()


class SharedGift(ndb.Model):
    READY = 0
    DONE = 1

    created = ndb.DateTimeProperty(auto_now_add=True)
    share_id = ndb.IntegerProperty(required=True)
    customer = ndb.KeyProperty(required=True)  # Who pays for cup
    recipient = ndb.KeyProperty()
    total_sum = ndb.IntegerProperty(required=True)
    #order_id = ndb.StringProperty(required=True)
    payment_type_id = ndb.StringProperty(required=True, choices=(PaymentType.CASH, PaymentType.CARD))
    #payment_id = ndb.StringProperty(required=True)
    status = ndb.IntegerProperty(choices=[READY, DONE], default=READY)

    def deactivate(self, company_id, venue_id, customer_id):
        from methods.iiko_api import add_bonus_to_customer, get_customer_by_id

        #add_bonus_to_customer(company_id, phone, venue_id, self.total_sum)
        share = Share.get_by_id(self.share_id)
        share.deactivate()
        self.status = self.DONE
        self.recipient_id = customer_id
        self.put()

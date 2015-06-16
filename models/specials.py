# coding=utf-8
import urllib

from google.appengine.ext import ndb
from models.iiko import Customer, PaymentType, Order, CompanyNew


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

        #add_bonus_to_customer(company_id, phone, venue_id, self.total_sum)
        share = Share.get_by_id(self.share_id)
        share.deactivate()
        self.status = self.DONE
        self.recipient_id = customer_id
        self.put()


class OrderSmsHistory(ndb.Model):
    sent = ndb.DateTimeProperty(auto_now_add=True)
    order = ndb.KeyProperty(Order, indexed=False)
    text = ndb.TextProperty()
    phone = ndb.TextProperty()
    company = ndb.KeyProperty(CompanyNew)
    success = ndb.BooleanProperty(default=True)


class AnalyticsLink(ndb.Model):
    @property
    def code(self):
        return self.key.id()

    name = ndb.StringProperty(required=True, indexed=False)
    ios_url = ndb.StringProperty(required=True, indexed=False)
    android_url = ndb.StringProperty(required=True, indexed=False)
    ios_default = ndb.BooleanProperty(required=True, indexed=False)

    @property
    def ga_page(self):
        return "download_%s" % self.name

    @property
    def default_url(self):
        return self.ios_url if self.ios_default else self.android_url

    @property
    def link_url(self):
        return "http://rbcn.mobi/get/%s" % self.code

    @property
    def qr_url(self):
        url = "%s?source=%s&medium=qr" % (self.link_url, self.name)
        return "http://chart.apis.google.com/chart?cht=qr&chs=540x540&chl=%s&chld=L|0" % urllib.quote(url)

    @classmethod
    def make_code(cls, name):
        import itertools
        for code in itertools.combinations(name, 3):
            code_str = ''.join(code)
            if not cls.get_by_id(code_str):
                return code_str

    @classmethod
    def create(cls, name='', **kwargs):
        link = cls(id=cls.make_code(name), name=name, **kwargs)
        link.put()
        return link

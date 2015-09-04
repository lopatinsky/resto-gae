# coding=utf-8
import urllib

from google.appengine.ext import ndb
import time
from models.iiko.customer import Customer
from models.iiko.order import Order
from models.iiko.company import PaymentType, CompanyNew


class MivakoGift(ndb.Model):
    sender = ndb.StringProperty()
    recipient = ndb.StringProperty()
    recipient_name = ndb.StringProperty()
    datetime = ndb.DateTimeProperty(auto_now_add=True)
    emailed = ndb.BooleanProperty(default=False)
    gift_item = ndb.StringProperty()


class Notification(ndb.Model):  # old class for storage pushes
    PUSH_NOTIFICATION = 0

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
    from methods.branch_io import FEATURE_CHOICES

    ACTIVE = 0
    INACTIVE = 1

    sender = ndb.KeyProperty(required=True, kind=Customer)
    share_type = ndb.IntegerProperty(required=True, choices=FEATURE_CHOICES)
    created = ndb.DateTimeProperty(auto_now_add=True)
    status = ndb.IntegerProperty(default=ACTIVE)
    urls = ndb.StringProperty(repeated=True)

    def deactivate(self):
        self.status = self.INACTIVE
        self.put()


class SharedBonus(ndb.Model):
    READY = 0
    DONE = 1
    CANCEL = 2

    sender = ndb.KeyProperty(required=True, kind=Customer)
    recipient = ndb.KeyProperty(required=True, kind=Customer)
    share_id = ndb.IntegerProperty(required=True)
    created = ndb.DateTimeProperty(auto_now_add=True)
    status = ndb.IntegerProperty(choices=[READY, DONE, CANCEL], default=READY)

    def cancel(self):
        from methods.parse_com import send_order_screen_push
        self.status = self.CANCEL
        self.put()
        send_order_screen_push(Order.query(Order.customer == self.recipient).get(), u'Вам начислены бонусы!')

    def deactivate(self, company):
        from methods.parse_com import send_order_screen_push
        from methods.iiko.customer import get_customer_by_phone, create_or_update_customer
        recipient = self.recipient.get()
        iiko_customer = get_customer_by_phone(company, recipient.phone)
        if 'httpStatusCode' in iiko_customer:
            iiko_customer = {
                'phone': recipient.phone,
                'balance': 0
            }
        iiko_customer['balance'] += company.invitation_settings.recipient_value
        create_or_update_customer(company, iiko_customer)
        sender = self.sender.get()
        iiko_customer = get_customer_by_phone(company, sender.phone)
        if 'httpStatusCode' in iiko_customer:
            iiko_customer = {
                'phone': sender.phone,
                'balance': 0
            }
        iiko_customer['balance'] += company.invitation_settings.sender_value
        create_or_update_customer(company, iiko_customer)
        self.status = self.DONE
        self.put()
        send_order_screen_push(Order.query(Order.customer == self.recipient).order(-Order.date).get(),
                               u'Вам начислены бонусы: %s! Спасибо, что заказываете у нас!' % company.invitation_settings.recipient_value,
                               head=company.app_title)
        send_order_screen_push(Order.query(Order.customer == self.sender).order(-Order.date).get(),
                               u'Вам начислены бонусы за приглашенного друга: %s!' % company.invitation_settings.sender_value,
                               head=company.app_title)


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
        url = self.link_url + "?m=qr"
        return "http://chart.apis.google.com/chart?cht=qr&chs=540x540&chl=%s&chld=L|0" % urllib.quote(url)

    @property
    def fb_url(self):
        return self.link_url + "?m=fb"

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


class ImageCache(ndb.Model):
    # key name is urlsafe_b64encoded image URL
    updated = ndb.DateTimeProperty(auto_now=True)
    last_modified = ndb.StringProperty(indexed=False)
    serving_url = ndb.StringProperty(indexed=False)


class News(ndb.Model):
    company_id = ndb.IntegerProperty(required=True)
    text = ndb.StringProperty(required=True, indexed=False)
    active = ndb.BooleanProperty(required=True, default=True)
    created_at = ndb.DateTimeProperty(auto_now_add=True, indexed=False)

    @classmethod
    def get(cls, company):
        return cls.query(cls.company_id == company.key.id(), cls.active == True).get()

    def dict(self):
        return {
            "id": self.key.id(),
            "text": self.text,
            "created_at": int(time.mktime(self.created_at.timetuple()))
        }

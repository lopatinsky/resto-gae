# coding=utf-8

from google.appengine.ext import ndb


class MivakoGift(ndb.Model):
    sender = ndb.StringProperty()
    recipient = ndb.StringProperty()
    recipient_name = ndb.StringProperty()
    datetime = ndb.DateTimeProperty(auto_now_add=True)
    emailed = ndb.BooleanProperty(default=False)
    gift_item = ndb.StringProperty()


class Notification(ndb.Model):
    PUSH_NOTIFICATION = 0

    #order_id = ndb.StringProperty(required=True)  old type of notification
    client_id = ndb.StringProperty(required=True)
    created = ndb.DateTimeProperty(auto_now_add=True)
    type = ndb.IntegerProperty(required=True)

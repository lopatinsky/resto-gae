from google.appengine.ext import ndb


class MivakoGift(ndb.Model):
    sender = ndb.StringProperty()
    recipient = ndb.StringProperty()
    recipient_name = ndb.StringProperty()
    datetime = ndb.DateTimeProperty(auto_now_add=True)

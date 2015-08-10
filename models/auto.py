from google.appengine.ext import ndb
from models.iiko import DeliveryTerminal

__author__ = 'dvpermyakov'


class AutoVenue(ndb.Model):
    token = ndb.StringProperty(required=True)
    delivery_terminal = ndb.KeyProperty(kind=DeliveryTerminal)

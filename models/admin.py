__author__ = 'dvpermyakov'

from google.appengine.ext import ndb


class Admin(ndb.Model):
    token = ndb.StringProperty()
    company_id = ndb.IntegerProperty()
    venue_name = ndb.StringProperty()
    venue_address = ndb.StringProperty()
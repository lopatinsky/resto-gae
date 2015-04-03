# coding=utf-8

__author__ = 'dvpermyakov'

from google.appengine.ext import ndb
from webapp2_extras.appengine.auth import models
from google.appengine.ext.ndb import polymodel

from models.iiko import Company


class User(polymodel.PolyModel, models.User):
    login = ndb.StringProperty()


class PushAdmin(User):
    PUSH_ADMIN = 'push_admin'

    company = ndb.KeyProperty(kind=Company, required=True)

    @classmethod
    def create(cls, login, company, password=None):
        auth_id = '%s:%s' % (cls.PUSH_ADMIN, login)
        values = {}
        if password:
            values['password_raw'] = password
        success, info = cls.create_user(auth_id=auth_id, login=login, company=company, **values)
        return success, info

    @classmethod
    def get_admin(cls, auth, login, password):
        auth_id = '%s:%s' % (cls.PUSH_ADMIN, login)
        return auth.get_user_by_password(auth_id, password)

    def delete(self):
        ids = ["%s.auth_id:%s" % (self.PUSH_ADMIN, i) for i in self.auth_ids]
        self.unique_model.delete_multi(ids)
        self.key.delete()


class Admin(ndb.Model):
    token = ndb.StringProperty(required=True)
    company_id = ndb.StringProperty(indexed=False, required=True)
    custom = ndb.JsonProperty()

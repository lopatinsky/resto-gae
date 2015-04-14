# coding=utf-8
__author__ = 'dvpermyakov'

from base import BaseHandler
from models.iiko import CompanyNew
from models.admin import PushAdmin
from webapp2_extras import security
import logging


class AutoCreatePushAdmins(BaseHandler):
    def post(self):
        companies = CompanyNew.query().fetch()
        for company in companies:
            if PushAdmin.query(PushAdmin.company == company.key).get():
                continue
            success, info = PushAdmin.create(company.app_title.strip().lower(), company.key, '0000')
            if not success:
                logging.info(info)
                self.abort(500)
        self.redirect_to('push_admin_main')


class ListPushAdmins(BaseHandler):
    def get(self):
        admins = PushAdmin.query().fetch()
        self.render('/push_admins/list.html', admins=admins)


class ChangeLoginPushAdmin(BaseHandler):

    def get(self, admin_id):
        admin_id = int(admin_id)
        admin = PushAdmin.get_by_id(admin_id)
        if not admin:
            self.abort(500)
        self.render('/push_admins/change_login.html', admin=admin)

    def post(self, admin_id):
        admin_id = int(admin_id)
        admin = PushAdmin.get_by_id(admin_id)
        if not admin:
            self.abort(500)
        login = self.request.get('login').strip().lower()
        success, info = PushAdmin.create(login, admin.company)
        if success:
            info.password = admin.password
            info.put()
            admin.delete()
            self.redirect_to('push_admin_main')
        else:
            self.render('/push_admin/change_login.html', admin=admin, error=u'Логин занят')


class ChangePasswordPushAdmin(BaseHandler):
    def get(self, admin_id):
        admin_id = int(admin_id)
        admin = PushAdmin.get_by_id(admin_id)
        if not admin:
            self.abort(500)
        self.render('/push_admins/change_password.html', admin=admin)

    def post(self, admin_id):
        admin_id = int(admin_id)
        admin = PushAdmin.get_by_id(admin_id)
        if not admin:
            self.abort(500)
        password = self.request.get('password')
        admin.password = security.generate_password_hash(password, length=12)
        admin.put()
        self.redirect_to('push_admin_main')
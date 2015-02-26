# coding=utf-8
__author__ = 'dvpermyakov'

from base import BaseHandler
from webapp2_extras.auth import InvalidAuthIdError, InvalidPasswordError
from models.admin import PushAdmin
from methods.auth import push_admin_user_required
import logging


class LoginHandler(BaseHandler):
    def success(self):
        self.redirect_to('pushes')

    def get(self):
        if self.user is not None:
            self.success()
        else:
            self.render('/mt/push_admins/login.html')

    def post(self):
        if self.user is not None:
            self.success()
        login = self.request.POST.get("login").lower().strip()
        password = self.request.POST.get("password")
        try:
            admin = PushAdmin.get_admin(self.auth, login, password)
            logging.info(admin)
        except (InvalidAuthIdError, InvalidPasswordError):
            self.render('/mt/push_admins/login.html', email=login, error=u"Неверный логин или пароль")
        else:
            self.success()


class LogoutHandler(BaseHandler):
    @push_admin_user_required
    def get(self):
        self.auth.unset_session()
        self.redirect_to('push_admin_login')
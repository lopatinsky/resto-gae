# coding=utf-8
import ast
import logging
import time
from methods.company import create
from methods.iiko.organization import get_orgs
from methods.maps import get_address_coordinates
from models.iiko.company import CompanyNew, IikoApiLogin, PlatiusLogin
from base import BaseHandler

__author__ = 'dvpermyakov'


class CompanyListHandler(BaseHandler):
    def _render(self, companies=None, logins=None, **kwargs):
        if not companies:
            companies = CompanyNew.query().fetch()
        if not logins:
            logins = [key.id() for key in IikoApiLogin.query().fetch(keys_only=True)]
        self.render('company/list.html', companies=companies, logins=logins, **kwargs)

    def get(self):
        self._render()

    def post(self):
        print self.request.body
        action = self.request.get("action")
        cls = None
        if action == "iiko_login":
            cls = IikoApiLogin
        elif action == "platius_login":
            cls = PlatiusLogin

        error = None
        login = self.request.get("login")
        password = self.request.get("password")

        if cls.get_by_id(login):
            error = u"Логин уже существует"
        if not error:
            login_key = cls(id=login, password=password).put()
            orgs = get_orgs(login, new_endpoints=(cls == IikoApiLogin))
            if not isinstance(orgs, list):
                login_key.delete()
                error = u"Неверный логин или пароль"
            else:
                time.sleep(1)  # wait for indexes
        self._render(error=error)


class CompanyCreateHandler(BaseHandler):
    def get(self):
        login = self.request.get("login")
        orgs = get_orgs(login, True)
        new_orgs = [org for org in orgs if not CompanyNew.get_by_iiko_id(org["id"])]
        self.render('company/create.html', login=login, orgs=new_orgs)

    def post(self):
        login = self.request.get("login")
        org_id = self.request.get("org_id")
        company = create(login, organization_id=org_id)
        self.redirect('/mt/company/%s' % company.key.id())


class CompanyEditHandler(BaseHandler):
    def get(self, company_id):
        c = CompanyNew.get_by_id(int(company_id))
        platius_logins = [key.id() for key in PlatiusLogin.query().fetch(keys_only=True)]
        self.render('company/edit.html', company=c, platius_logins=platius_logins)

    def post(self, company_id):
        c = CompanyNew.get_by_id(int(company_id))
        c.app_title = self.request.get("app_title")
        c.description = self.request.get("description")
        c.address = self.request.get("address")
        try:
            c.latitude, c.longitude = get_address_coordinates(c.address)
        except Exception as e:
            logging.exception(e)
        c.phone = self.request.get("phone")
        c.site = self.request.get("site")
        c.email = self.request.get("email")
        c.cities = self.request.get("cities").split(",")
        c.min_order_sum = int(self.request.get("min_order_sum"))
        c.schedule = ast.literal_eval(self.request.get("schedule"))
        c.new_endpoints = bool(self.request.get("new_endpoints"))
        c.is_iiko_system = bool(self.request.get("platius"))
        c.platius_login = self.request.get("platius_login")
        c.platius_org_id = self.request.get("platius_id")
        c.alpha_login = self.request.get("alpha_login")
        c.alpha_pass = self.request.get("alpha_pass")
        c.support_emails = self.request.get("support_emails").split(",")
        c.app_name = self.request.get("user_agent").split(",")
        c.put()
        platius_logins = [key.id() for key in PlatiusLogin.query().fetch(keys_only=True)]
        self.render('company/edit.html', company=c, platius_logins=platius_logins, success=True)

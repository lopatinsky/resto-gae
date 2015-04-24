__author__ = 'dvpermyakov'

from base import BaseHandler
from models.iiko import CompanyNew
from methods.push_venues import push_venues
from methods.auth import push_admin_user_required
from models.specials import MassPushHistory
from webapp2_extras import jinja2
import logging


class PushSendingHandler(BaseHandler):
    @push_admin_user_required
    def get(self):
        companies = CompanyNew.query().fetch()
        self.render('/mt/pushes.html', companies=companies, has_choices=False, user=self.user)

    @push_admin_user_required
    def post(self):
        logging.info(self.request.POST)

        text = self.request.get('text')
        head = self.request.get('head')
        android_avail = bool(self.request.get('android'))
        ios_avail = bool(self.request.get('ios'))
        chosen_companies = [self.user.company.id()]

        push_venues(chosen_companies, text, head, android_avail, ios_avail, self.user.login, jinja2.get_jinja2(app=self.app))

        self.redirect_to('admin_push_history')


class PushHistoryHandler(BaseHandler):
    @push_admin_user_required
    def get(self):
        menu_reload = 'menu_reload' in self.request.params
        mass_pushes = MassPushHistory.query().order(-MassPushHistory.created).fetch()
        for push in mass_pushes[:]:
            if self.user.company.id() not in push.company_ids or len(push.company_ids) > 1:
                mass_pushes.remove(push)
                continue
            push.companies = ''.join(['%s, ' % CompanyNew.get_by_id(company_id).app_title
                                      for company_id in push.company_ids])
            push.android_number = len(push.android_channels)
            push.ios_number = len(push.ios_channels)
        self.render('mt/pushes_history.html', history=mass_pushes, user=self.user, menu_reload=menu_reload)
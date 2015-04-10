# coding=utf-8

__author__ = 'dvpermyakov'

from base import BaseHandler
from models.iiko import CompanyNew
from methods.push_venues import push_venues
from models.specials import MassPushHistory
from webapp2_extras import jinja2
import logging


class PushSendingHandler(BaseHandler):
    def get(self):
        companies = CompanyNew.query().fetch()
        self.render('/pushes.html', companies=companies, has_choices=True)

    def post(self):
        logging.info(self.request.POST)

        text = self.request.get('text')
        head = self.request.get('head')
        companies = CompanyNew.query().fetch()
        android_avail = bool(self.request.get('android'))
        ios_avail = bool(self.request.get('ios'))
        chosen_companies = [company.key.id() for company in companies if bool(self.request.get(str(company.key.id())))]

        push_venues(chosen_companies, text, head, android_avail, ios_avail, 'admins', jinja2.get_jinja2(app=self.app))

        self.redirect_to('mt_push_history')


class PushHistoryHandler(BaseHandler):
    def get(self):
        mass_pushes = MassPushHistory.query().order(-MassPushHistory.created).fetch()
        for push in mass_pushes:
            push.companies = ''.join(['%s, ' % CompanyNew.get_by_id(company_id).name for company_id in push.company_ids])
            push.android_number = len(push.android_channels)
            push.ios_number = len(push.ios_channels)

        self.render('/pushes_history.html', history=mass_pushes)
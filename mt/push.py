__author__ = 'dvpermyakov'

from base import BaseHandler
from models.iiko import Company
from methods.push_venues import push_venues
import logging


class PushSendingHandler(BaseHandler):
    def get(self):
        companies = Company.query().fetch()
        self.render('/pushes.html', companies=companies, has_choices=True)

    def post(self):
        logging.info(self.request.POST)

        text = self.request.get('text')
        head = self.request.get('head')
        companies = Company.query().fetch()
        android_avail = bool(self.request.get('android'))
        ios_avail = bool(self.request.get('ios'))
        chosen_companies = [company.key.id() for company in companies if bool(self.request.get(str(company.key.id())))]

        result = push_venues(chosen_companies, text, head, android_avail, ios_avail)

        self.render('/pushes_result.html', result=result)
# coding=utf-8
import time
from .base import BaseHandler
from models.specials import AnalyticsLink


class AnalyticsLinkListHandler(BaseHandler):
    def get(self):
        links = AnalyticsLink.query().fetch()
        self.render('qr/list.html', links=links)

    def post(self):
        name = self.request.get('name')
        ios_url = self.request.get('ios_url')
        android_url = self.request.get('android_url')
        ios_default = bool(self.request.get('ios_default'))
        AnalyticsLink.create(
            name=name,
            ios_url=ios_url,
            android_url=android_url,
            ios_default=ios_default
        )

        time.sleep(1)
        self.redirect(self.request.uri)


class AnalyticsLinkEditHandler(BaseHandler):
    def get(self, code):
        link = AnalyticsLink.get_by_id(code)
        if not link:
            self.abort(404)
        self.render('qr/edit.html', link=link)

    def post(self, code):
        link = AnalyticsLink.get_by_id(code)
        if not link:
            self.abort(404)
        link.ios_url = self.request.get('ios_url')
        link.android_url = self.request.get('android_url')
        link.ios_default = bool(self.request.get('ios_default'))
        link.put()
        self.redirect('/mt/qr')
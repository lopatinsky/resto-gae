# coding=utf-8
import datetime
import logging

import webapp2
from .lib_ga import ga_track_event, ga_track_page
from models.specials import AnalyticsLink


GA_TID = "UA-57935469-8"


class GATrackBaseRequestHandler(webapp2.RequestHandler):
    def __init__(self, request=None, response=None):
        super(GATrackBaseRequestHandler, self).__init__(request, response)
        self.ga_headers = {'User-Agent': self.request.headers["User-Agent"]}
        self.cid = self.get_cid()

    def track_event(self, category, action, label=None, value=None):
        self.cid = ga_track_event(GA_TID, category, action, label=label, value=value, cid=self.cid, v=1,
                                  req_headers=self.ga_headers)

    def get_cid(self):
        cid = None
        ga = self.request.cookies.get('_ga')
        if ga:
            cid = '.'.join(ga.split('.')[-2:])
        return cid


class GATrackRequestHandler(GATrackBaseRequestHandler):
    def __init__(self, request=None, response=None):
        super(GATrackRequestHandler, self).__init__(request=request, response=response)
        self.campaign = {}

    def page_titles(self, *args, **kwargs):
        raise NotImplementedError()

    def action(self, *args, **kwargs):
        raise NotImplementedError()

    def set_campaign(self, *args, **kwargs):
        pass

    def get(self, *args, **kwargs):

        dh = self.request.host
        dp = self.request.path_qs
        titles = self.page_titles(*args, **kwargs)
        self.set_campaign(*args, **kwargs)

        for dt in titles:
            self.cid = ga_track_page(GA_TID, dh, dp, dt, self.cid, req_headers=self.ga_headers, campaign=self.campaign)
        if self.cid is not None:
            cookie = '.'.join(('GA1', str(dh.count('.')), self.cid))
            expires = datetime.datetime.utcnow() + datetime.timedelta(days=365 * 2)
            self.response.set_cookie('_ga', cookie, path='/', expires=expires)

        self.action(*args, **kwargs)


class GATrackDownloadHandler(GATrackRequestHandler):
    link = None

    def set_campaign(self, app):
        self.campaign["cn"] = "link_%s" % self.link.name

        source = self.request.get("source") or self.link.name
        self.campaign["cs"] = source

        medium = self.request.get("medium") or self.request.get("m")
        if medium:
            self.campaign["cm"] = medium

    def dispatch(self):
        app = self.request.route_kwargs["app"]
        self.link = AnalyticsLink.get_by_id(app)
        if self.link:
            super(GATrackDownloadHandler, self).dispatch()
        else:
            self.abort(404)

    def page_titles(self, app):
        return [self.link.ga_page]

    def redirect(self, uri, *args, **kwargs):
        if isinstance(uri, unicode):
            uri = uri.encode('utf-8')
        super(GATrackDownloadHandler, self).redirect(uri, *args, **kwargs)

    def action(self, app):
        ua = self.request.headers['User-Agent']
        if 'Android' in ua:
            self.track_event(self.link.ga_page, 'download_auto', 'android')
            self.redirect(self.link.android_url)
        elif "iPhone" in ua or "iPad" in ua or "iPad" in ua:
            self.track_event(self.link.ga_page, 'download_auto', 'ios')
            self.redirect(self.link.ios_url)
        else:
            if "Branch" in ua or "facebookexternalhit" in ua:
                logging.info("crawler (branch/fb): do not track")
            else:
                self.track_event(self.link.ga_page, 'download_auto', 'other')
            self.redirect(self.link.default_url)

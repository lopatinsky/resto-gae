import datetime
import webapp2
from .lib_ga import ga_track_event, ga_track_page


GA_TID = "UA-57935469-7"


APPS = {
    # 0: app identifier
    # 1: ios url
    # 2: android url
    # 3: True -> ios url by default, False -> android
    "slr": (
        "sushilar",
        "http://sushilar.ru/",
        "https://play.google.com/store/apps/details?id=com.sushilar",
        False
    ),
    "oex": (
        "orange_express",
        "http://pizza-sushi.com/",
        "https://play.google.com/store/apps/details?id=com.orangexpress",
        False
    ),
    "cat": (
        "coffee_city",
        "http://coffeeandthecity.ru/",
        "http://coffeeandthecity.ru/",
        True
    ),
}


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
    def page_titles(self, *args, **kwargs):
        raise NotImplementedError()

    def action(self, *args, **kwargs):
        raise NotImplementedError()

    def get(self, *args, **kwargs):

        dh = self.request.host
        dp = self.request.path_qs
        titles = self.page_titles(*args, **kwargs)

        for dt in titles:
            self.cid = ga_track_page(GA_TID, dh, dp, dt, self.cid, req_headers=self.ga_headers)
        if self.cid is not None:
            cookie = '.'.join(('GA1', str(dh.count('.')), self.cid))
            expires = datetime.datetime.utcnow() + datetime.timedelta(days=365 * 2)
            self.response.set_cookie('_ga', cookie, path='/', expires=expires)

        self.action(*args, **kwargs)


class GATrackDownloadHandler(GATrackRequestHandler):
    page = None
    ios_url = None
    android_url = None
    default_url = None

    def _load_app_info(self, app_info):
        name, self.ios_url, self.android_url, default_ios = app_info
        self.default_url = self.ios_url if default_ios else self.android_url
        self.page = "download_%s" % name
        print self.__dict__

    def dispatch(self):
        app = self.request.route_kwargs["app"]
        if app in APPS:
            self._load_app_info(APPS[app])
            super(GATrackDownloadHandler, self).dispatch()
        else:
            self.abort(404)

    def page_titles(self, app):
        return [self.page]

    def action(self, app):
        ua = self.request.headers['User-Agent']
        if 'Android' in ua:
            self.track_event(self.page, 'download_auto', 'android')
            self.redirect(self.android_url)
        elif "iPhone" in ua or "iPad" in ua or "iPad" in ua:
            self.track_event(self.page, 'download_auto', 'ios')
            self.redirect(self.ios_url)
        else:
            self.track_event(self.page, 'download_auto', 'other')
            self.redirect(self.default_url)

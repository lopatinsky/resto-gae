# coding=utf-8
import logging

from config import config
import json
from google.appengine.api import urlfetch
import webapp2


class BaseHandler(webapp2.RequestHandler):
    def dispatch(self):
        # fuckup OE iOS 2.0.3
        if config.DEBUG and self.request.headers['User-Agent'].startswith("OrangeExpress/2.0.3 "):
            logging.info('redirect')
            result = urlfetch.fetch(
                'http://empatika-resto.appspot.com' + self.request.path_qs,
                self.request.body,
                self.request.method,
                self.request.headers,
                deadline=55
            )
            self.response.status_int = result.status_code
            self.response.headers['Content-Type'] = result.headers['Content-Type']
            self.response.write(result.content)
            return
        # fuckup end

    def render_json(self, d):
        self.response.headers['Content-Type'] = 'application/json'
        self.response.out.write(json.dumps(d, separators=(',', ':')))

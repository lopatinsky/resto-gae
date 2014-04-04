import json
import webapp2

__author__ = 'phil'


class BaseHandler(webapp2.RequestHandler):
    def render_json(self, d):
        self.response.headers['Content-Type'] = 'application/json'
        self.response.out.write(json.dumps(d, separators=(',', ':')))
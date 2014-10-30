import json
import webapp2
from models.iiko import Company

__author__ = 'phil'


class BaseHandler(webapp2.RequestHandler):
    company = None
    _company_required = False

    def render_json(self, d):
        self.response.headers['Content-Type'] = 'application/json'
        self.response.out.write(json.dumps(d, separators=(',', ':')))

    def dispatch(self):
        ua = self.request.headers["User-Agent"]
        name = ua.split('/', 1)[0].lower().strip()
        self.company = Company.query(Company.app_name == name).get()
        if self._company_required and not self.company:
            self.abort(400)
        return super(BaseHandler, self).dispatch()

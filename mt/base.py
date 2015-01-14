__author__ = 'dvpermyakov'

# coding=utf-8

import json
import webapp2
from models.iiko import Company
from webapp2_extras import jinja2
from webapp2 import cached_property


class BaseHandler(webapp2.RequestHandler):
    company = None
    _company_required = False

    def render_json(self, d):
        self.response.headers['Content-Type'] = 'application/json'
        self.response.out.write(json.dumps(d, separators=(',', ':')))

    @cached_property
    def jinja2(self):
        return jinja2.get_jinja2(app=self.app)

    def render(self, template_name, **values):
        rendered = self.jinja2.render_template('mt/' + template_name, **values)
        self.response.write(rendered)

    def dispatch(self):
        ua = self.request.headers["User-Agent"]
        name = ua.split('/', 1)[0].lower().strip()
        self.company = Company.query(Company.app_name == name).get()
        if self._company_required and not self.company:
            self.abort(400)
        return super(BaseHandler, self).dispatch()
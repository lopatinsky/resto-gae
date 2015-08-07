# coding=utf-8
from webapp2 import RequestHandler
from webapp2_extras import jinja2

from register import RegisterHandler
from news import NewsHandler


class MainHandler(RequestHandler):
    def get(self):
        self.response.write(jinja2.get_jinja2(app=self.app).render_template("landing.html"))

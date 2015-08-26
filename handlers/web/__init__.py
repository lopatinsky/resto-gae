# coding=utf-8

from webapp2 import cached_property, RequestHandler
from webapp2_extras import jinja2
from methods.web_i18n import lang_selector, make_getter


class BaseHandler(RequestHandler):
    @cached_property
    def jinja2(self):
        return jinja2.get_jinja2(app=self.app)

    def render(self, template_name, **values):
        lang = lang_selector(self.request)
        values.update({
            "lang": lang,
            "t": make_getter(lang)
        })
        rendered = self.jinja2.render_template(template_name, **values)
        self.response.write(rendered)


class LandingHandler(BaseHandler):
    def get(self):
        self.render("landing.html")

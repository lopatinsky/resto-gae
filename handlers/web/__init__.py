# coding=utf-8

from webapp2 import cached_property, RequestHandler
from webapp2_extras import jinja2

from methods import excel
from methods.iiko.menu import get_menu
from methods.web_i18n import lang_selector, make_getter
from models.iiko.company import CompanyNew


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


class ViewMenuHandler(BaseHandler):
    def get(self, company_id):
        company = CompanyNew.get_by_id(int(company_id))
        menu = get_menu(company.iiko_org_id, force_reload=True)

        def process_category(category, names, dst):
            names.append(category['name'])
            if category['products']:
                dst.append((" > ".join(names), category['products']))
            for subcat in category['children']:
                process_category(subcat, names, dst)
            names.pop()

        result = []
        for cat in menu:
            process_category(cat, [], result)

        self.render('/mt/reports/view_menu.html', menu=result)



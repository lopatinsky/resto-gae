from api.base import BaseHandler
from iiko import Company

__author__ = 'mihailnikolaev'


class AddCompanyRequestHandler(BaseHandler):
    def post(self):
        name = self.request.get('name')
        password = self.request.get('password')

        comp = Company()
        comp.name = name
        comp.password = password
        comp.put()

        self.render_json({"organization_id": comp.get_id()})
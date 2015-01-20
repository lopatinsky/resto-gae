__author__ = 'dvpermyakov'


from base import BaseHandler
from models import iiko


class CreateCompaniesLinks(BaseHandler):
    def get(self):
        companies = iiko.Company.query().fetch()
        self.render('company_links.html', companies=companies)


class CompanySettingsHandler(BaseHandler):
    def get(self, company_id):
        delivery_types = []
        company = iiko.Company.get_by_id(int(company_id))
        for delivery_type in company.delivery_types:
            delivery_types.append(delivery_type.get())
        self.render('company.html', delivery_types=delivery_types, company_name=company.name)

    def post(self, company_id):
        for delivery_type in iiko.Company._get_by_id(int(company_id)).delivery_types:
            available = bool(self.request.get(str(delivery_type.id())))
            ndb_delivery_type = delivery_type.get()
            ndb_delivery_type.available = available
            ndb_delivery_type.put()
        companies = iiko.Company.query().fetch()
        self.render('company_links.html', companies=companies)
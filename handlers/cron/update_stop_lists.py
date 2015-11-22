# coding=utf-8
from webapp2 import RequestHandler

from methods.iiko.menu import get_company_stop_lists
from models.iiko.company import CompanyNew


class UpdateStopListsHandler(RequestHandler):
    def get(self):
        companies = CompanyNew.query(CompanyNew.iiko_stop_lists_enabled == True).fetch()
        for company in companies:
            get_company_stop_lists(company, force_reload=True)

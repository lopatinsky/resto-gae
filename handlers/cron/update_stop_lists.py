# coding=utf-8
from webapp2 import RequestHandler

from methods.iiko.menu import update_company_stop_lists
from models.iiko.company import CompanyNew


class UpdateStopListsHandler(RequestHandler):
    def get(self):
        companies = CompanyNew.query(CompanyNew.iiko_stop_lists_enabled == True).fetch()
        for company in companies:
            update_company_stop_lists(company)

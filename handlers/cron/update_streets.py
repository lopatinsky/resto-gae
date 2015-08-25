# coding=utf-8

from google.appengine.ext import deferred
from webapp2 import RequestHandler
from methods.iiko.address import get_cities_and_streets
from models.iiko import CompanyNew


def _load_streets(company_key):
    get_cities_and_streets(company_key.get(), force_update=True)


class UpdateStreetsHandler(RequestHandler):
    def get(self):
        for company_key in CompanyNew.query().fetch(keys_only=True):
            deferred.defer(_load_streets, company_key)

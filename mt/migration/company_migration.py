# coding=utf-8

from methods import iiko_api
from models.iiko import Company, CompanyNew, IikoApiLogin
from mt.base import BaseHandler


class CreateNewCompaniesHandler(BaseHandler):
    def get(self):
        companies = Company.query().fetch()
        for c in companies:
            IikoApiLogin(id=c.name, password=c.password).put()

            venue, = iiko_api.get_venues(c.key.id())

            dct = {
                k: getattr(c, k)
                for k in Company._properties
                if k not in ('name', 'password')
            }
            CompanyNew(
                id=c.key.id(),
                menu=venue.menu,
                address=venue.address,
                latitude=venue.latitude,
                longitude=venue.longitude,
                iiko_login=c.name,
                iiko_org_id=venue.venue_id,
                **dct
            ).put()

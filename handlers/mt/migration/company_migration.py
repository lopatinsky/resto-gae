# coding=utf-8
from google.appengine.api.datastore_types import GeoPt

from methods.iiko.delivery_terminal import get_delivery_terminals
from models.iiko import CompanyNew, IikoApiLogin, DeliveryTerminal

try:
    from models.iiko import Company
except ImportError:
    Company = None
from handlers.mt.base import BaseHandler


class CreateNewCompaniesHandler(BaseHandler):
    def get(self):
        companies = Company.query().fetch()
        for c in companies:
            IikoApiLogin(id=c.name, password=c.password).put()

            venue = None

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
                payment_types=venue.payment_types,
                iiko_login=c.name,
                iiko_org_id=venue.venue_id,
                **dct
            ).put()

            dts = get_delivery_terminals(venue.venue_id)
            for dt in dts:
                DeliveryTerminal(
                    id=dt['deliveryTerminalId'],
                    active=dt['deliveryTerminalId'] != 'd7fd5599-814a-79be-0146-b83a4192096f',
                    phone=c.phone or '',
                    company_id=c.key.id(),
                    iiko_organization_id=venue.venue_id,
                    name=dt['deliveryRestaurantName'],
                    address=dt['address'],
                    location=GeoPt(venue.latitude, venue.longitude)
                ).put()

from google.appengine.ext import ndb
from methods.iiko.delivery_terminal import get_delivery_terminals
from methods.maps import get_address_coordinates
from config import config
from methods.iiko.organization import get_org, get_orgs
from models.iiko import IikoApiLogin, CompanyNew, DeliveryType, PaymentType, DeliveryTerminal

__author__ = 'dvpermyakov'


def _load_delivery_terminals(company):
    iiko_delivery_terminals = get_delivery_terminals(company)
    dts = map(lambda iiko_delivery_terminal: DeliveryTerminal(
        id=iiko_delivery_terminal['deliveryTerminalId'],
        company_id=company.key.id(),
        iiko_organization_id=company.iiko_org_id,
        active=True,
        name=iiko_delivery_terminal['deliveryRestaurantName'],
        phone=company.phone,
        address=iiko_delivery_terminal['address'],
        location=ndb.GeoPt(company.latitude, company.longitude)
    ), iiko_delivery_terminals)
    ndb.put_multi(dts)
    return dts


def create(login, password, company_id=None, organization_id=None, new_endpoints=True):
    IikoApiLogin.get_or_insert(login, password=password)

    company = CompanyNew(id=company_id)
    company.new_endpoints = new_endpoints
    company.iiko_login = login

    if organization_id:
        organization = get_org(login, organization_id, new_endpoints)
        company.iiko_org_id = organization_id
    else:
        organization = get_orgs(login, new_endpoints)[0]
        company.iiko_org_id = organization['id']
    company.app_title = organization['name']
    company.address = organization['address'] or organization['contact']['location']
    company.latitude, company.longitude = get_address_coordinates(company.address)

    delivery_types = [
        DeliveryType(available=True, delivery_id=0, name="delivery"),
        DeliveryType(available=False, delivery_id=1, name="self"),
    ]
    company.delivery_types = ndb.put_multi(delivery_types)

    payment_types = [
        PaymentType(available=True, type_id=1, name="cash", iiko_uuid="CASH"),
        PaymentType(available=config.DEBUG, type_id=2, name="card", iiko_uuid="ECARD")
    ]
    company.payment_types = ndb.put_multi(payment_types)

    if config.DEBUG:
        company.alpha_login = "empatika_autopay-api"
        company.alpha_pass = "empatika_autopay"
    company.put()

    _load_delivery_terminals(company)
    return company

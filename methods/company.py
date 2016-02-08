# coding=utf-8
import logging
import re
from google.appengine.ext import ndb
from methods.iiko.delivery_terminal import get_delivery_terminals
from methods.maps import get_address_coordinates
from config import config
from methods.iiko.organization import get_org, get_orgs
from models.iiko import IikoApiLogin, CompanyNew, DeliveryType, PaymentType, DeliveryTerminal
from models.iiko.company import AdditionalCategory

__author__ = 'dvpermyakov'

_guid_pattern = "^[0-9A-F]{8}-[0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{12}$"
_guid_regex = re.compile(_guid_pattern, re.IGNORECASE)


def _load_delivery_terminals(company):
    iiko_delivery_terminals = get_delivery_terminals(company)
    dts = map(lambda iiko_delivery_terminal: DeliveryTerminal.get_or_insert(
        iiko_delivery_terminal['deliveryTerminalId'],
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


def create(login, password=None, company_id=None, organization_id=None, new_endpoints=True):
    if not IikoApiLogin.get_by_id(login):
        if not password:
            raise Exception("Login does not exist, so password is required")
        IikoApiLogin(id=login, password=password).put()

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
    company.latitude, company.longitude = 0, 0
    if company.address:
        try:
            company.latitude, company.longitude = get_address_coordinates(company.address)
        except Exception as e:
            logging.exception(e)

    delivery_types = [
        DeliveryType(available=True, delivery_id=DeliveryType.DELIVERY, name="delivery"),
        DeliveryType(available=False, delivery_id=DeliveryType.SELF, name="self"),
        DeliveryType(available=False, delivery_id=DeliveryType.IN_CAFE, name="in cafe"),
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


def parse_additional_categories(str_categories):
    logging.info(repr(str_categories))
    lines = [l.strip() for l in str_categories.split("\n")]
    result = []
    for line in lines:
        logging.info(repr(line))
        if not line:
            continue
        if _guid_regex.match(line):
            logging.info('%s is a GUID, appending', line)
            if len(result) == 0:
                result.append(AdditionalCategory(title=u'Популярное'))
            result[-1].item_ids.append(line)
        else:
            if "|" in line:
                title, url = line.rsplit("|", 1)
            else:
                title, url = line, None
            logging.info('New category with title %s', title)
            result.append(AdditionalCategory(title=title, image_url=url))
    return [c for c in result if c.item_ids]

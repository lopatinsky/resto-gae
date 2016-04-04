import logging

from google.appengine.api import memcache

from methods.iiko.customer import get_customer_by_phone
from models.iiko import Customer, BonusCardHack

__author__ = 'dvpermyakov'


def get_iiko_customer_from_memcache(iiko_org_id, phone):
    return memcache.get(iiko_org_id + phone)


def set_iiko_customer_to_memcache(iiko_org_id, phone, iiko_customer):
    memcache.set(iiko_org_id + phone, iiko_customer, time=10*60)
    return


def delete_iiko_customer_from_memcache(iiko_org_id, phone):
    memcache.delete(iiko_org_id + phone)
    return


def _update_customer_id(customer, iiko_customer):
    iiko_customer_id = iiko_customer.get('id', None)
    if iiko_customer_id:
        customer.customer_id = iiko_customer_id


def update_customer_id(company, customer):
    phone, card_customer_id = BonusCardHack.get(customer.phone)
    if card_customer_id:
        customer.customer_id = card_customer_id
    elif phone:
        iiko_customer = get_iiko_customer_from_memcache(company.iiko_org_id, phone)
        if not iiko_customer:
            iiko_customer = get_customer_by_phone(company, phone)
            set_iiko_customer_to_memcache(company.iiko_org_id, phone, iiko_customer)
        else:
            logging.info('iiko customer id found in cache: ' + str(iiko_customer))
        _update_customer_id(customer, iiko_customer)


def get_resto_customer(company, customer_id):
    customer = None
    if customer_id:
        customer = Customer.customer_by_customer_id(customer_id)
        if not customer:
            customer = Customer.get_by_id(customer_id)
    if not customer:
        customer = Customer(id=Customer.generate_customer_id())
    customer.company = company.key
    return customer


def set_customer_info(company, customer, name, headers, phone, custom_data=None):
    customer.company = company.key
    customer.phone = phone
    customer.name = name
    customer.user_agent = headers['User-Agent']
    customer.custom_data = custom_data

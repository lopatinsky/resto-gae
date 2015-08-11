from methods.iiko.customer import get_customer_by_phone
from models.iiko import Customer, BonusCardHack

__author__ = 'dvpermyakov'


def _update_customer_id(customer, iiko_customer):
    iiko_customer_id = iiko_customer.get('id', None)
    if iiko_customer_id :
        customer.customer_id = iiko_customer_id


def update_customer_id(company, customer):
    phone, card_customer_id = BonusCardHack.get(customer.phone)
    if card_customer_id:
        customer.customer_id = card_customer_id
    elif phone:
        _update_customer_id(customer, get_customer_by_phone(company, phone))


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

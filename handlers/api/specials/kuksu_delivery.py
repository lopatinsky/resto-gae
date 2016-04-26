# coding=utf-8
from methods.iiko.menu import prepare_items, get_product_from_menu
from methods.iiko.promo import calc_sum
from models.iiko.company import CompanyNew

KUKSU_DELIVERY_PRODUCT_ID = '910c67ce-976c-4b26-b42a-1fd3124e1354'


def check_delivery(order):
    return order.sum < 2000


def get_delivery_sum():
    item = get_product_from_menu(CompanyNew.KUKSU, product_id=KUKSU_DELIVERY_PRODUCT_ID)
    return item['price']


def check_and_add_delivery(company, order):
    if check_delivery(order):
        delivery_item = {
            'id': KUKSU_DELIVERY_PRODUCT_ID,
            'amount': 1
        }
        prepare_items(company, [delivery_item])
        order.items.append(delivery_item)
        order.initial_sum = order.sum = calc_sum(order.items, company.iiko_org_id)
        return True
    return False

# coding=utf-8
import json
import logging
from datetime import datetime

from handlers.api.specials.hardcoded_promos import HARDCODED_PROMOS
from methods.iiko.base import get_request, post_request
from methods.iiko.menu import get_product_from_menu, list_menu
from methods.specials.lpq import apply_lpq_discounts
from models.iiko import CompanyNew
from models.iiko.delivery_terminal import DeliveryTerminal

__author__ = 'dvpermyakov'


def get_iikonet_payment_type(order):
    _default = "INET"
    if order.venue_id == CompanyNew.ORANGE_EXPRESS:
        city = order.address.get("city") if order.address else None
        return {
            u"Егорьевск": "INET1",
            u"Одинцово": "INET2",
            u"Домодедово": "INET3",
            u"Подольск": "INET4",
            u"Климовск": "INET4",
            u"Авиагородок": "INET6",
        }.get(city, _default)
    elif order.venue_id == CompanyNew.SUSHILAR:
        logging.info(order.delivery_terminal_id)
        if order.delivery_terminal_id == '088bab87-eb17-6deb-0147-a9d8fd1184b5':  # ПАРИНА
            return 'PA'
        elif order.delivery_terminal_id == '088bab87-eb17-6deb-0147-a9f3a0380c68':  # ХАДИ-ТАКТАШ
            return 'HA'
        elif order.delivery_terminal_id == '088bab87-eb17-6deb-0147-a9f3a038cf7e':  # ВОССТАНИЯ
            return 'VO'
        elif order.delivery_terminal_id == '0d81e7d2-daf2-f7a8-0147-aa2667ef2e82':  # ЯМАШЕВА
            return 'YAYA'
        elif order.delivery_terminal_id == '0e7bd2d0-c748-b906-0147-ee6188bfbb7d':  # БЕГИЧЕВА
            return 'BI'
        elif order.delivery_terminal_id == '2e613146-b7bb-94e1-0149-3cf1753e76e2':  # АДОРАТСКОГО
            return 'AO'
        else:
            return 'PA'  # default
    if not order.is_delivery:
        dt = DeliveryTerminal.get_by_id(order.delivery_terminal_id)
        if dt.platius_payment_code:
            return dt.platius_payment_code
    return _default


def set_gifts(order, order_from_dict, gifts):

    discount_sum = 0
    for gift in gifts:
        order.items.append({
            'code': gift['code'],
            'name': gift['name'],
            'amount': gift['amount'],
            'sum': gift['sum'],
            'id': gift['id']
        })
        #order.sum += gift['price'] * gift['amount']
        discount_sum += gift['price'] * gift['amount']
    add_bonus_to_payment(order_from_dict, discount_sum, False)


def set_discounts(order, order_from_dict, promos):
    order.discount_sum = 0.0

    if order.venue_id == CompanyNew.HLEB:
        apply_lpq_discounts(order)

    def get_items(product_code):
        return [item for item in order.items if item['code'] == product_code]

    non_platius_discount = order.discount_sum

    for dis_info in promos.get('discountInfo', []):
        for detail in dis_info.get('details', []):
            if detail.get('discountSum'):
                items = get_items(detail.get('code'))
                discount_for_code = detail['discountSum']
                for item in items:
                    item.setdefault('discount_sum', 0)
                    item_discount = min(item['sum'], discount_for_code)
                    if item_discount > item['sum']:
                        item_discount = item['sum']
                    item['discount_sum'] += item_discount
                    item['sum'] -= item_discount
                    order.discount_sum += item_discount
                    discount_for_code -= item_discount
                if discount_for_code > 0:
                    logging.warning('discounts not found!')

    if non_platius_discount:
        add_bonus_to_payment(order_from_dict, non_platius_discount, True, False)
    ret = add_bonus_to_payment(order_from_dict, order.discount_sum - non_platius_discount, True)
    logging.info("set_discount finished: %s", order_from_dict['paymentItems'])
    return ret


def add_bonus_to_payment(order, bonus_sum, is_deducted, is_platius=True):
    def get_payment(order, name):
        for p_item in order['paymentItems']:
            if p_item['paymentType']['name'] == name:
                return p_item
        return None

    p_bonus = get_payment(order, 'iiko.Net')
    if p_bonus:
        if is_platius:
            p_bonus['sum'] += bonus_sum
        if is_deducted:
            get_payment(order, 'not iiko.Net')['sum'] -= bonus_sum
            order['fullSum'] -= bonus_sum
        return True
    else:
        return False


def calc_sum(items, iiko_org_id):
    menu = list_menu(iiko_org_id)
    menu_dict = {}
    mods_dict = {}
    for p in menu:
        menu_dict[p['productId']] = p
        for mod in p['single_modifiers']:
            mods_dict[mod['id']] = mod
        for group in p['modifiers']:
            for mod in group['items']:
                mods_dict[mod['id']] = mod

    result = 0.0
    for item in items:
        result += menu_dict[item['id']]['price'] * item['amount']
        for mod in item.get('modifiers', []):
            result += mods_dict[mod['id']]['price'] * mod['amount'] * item['amount']

    return result


def get_venue_promos(org_id):
    if org_id in HARDCODED_PROMOS:
        return HARDCODED_PROMOS[org_id]

    url = '/organization/%s/marketing_campaigns' % org_id
    company = CompanyNew.get_by_iiko_id(org_id)
    if not company.is_iiko_system:
        return []
    promos = json.loads(get_request(company, url, {}, force_platius=True))
    result = []
    for promo in promos:
        if not promo['name']:
            continue
        promo_start = promo_end = None
        if promo['start']:
            promo_start = datetime.strptime(promo['start'], '%Y-%m-%d')
            if datetime.now() < promo_start:
                continue
        if promo['end']:
            promo_end = datetime.strptime(promo['end'], '%Y-%m-%d')
            if datetime.now() > promo_end:
                continue
        result.append({
            'id': promo['id'],
            'name': promo['name'] if promo['name'] else '',
            'description': promo['description'] if promo['description'] else '',
            'image_url': promo['imageUrl'],
            'display_type': 3,
            'start': (promo_start - datetime(1970, 1, 1)).total_seconds() if promo_start else None,
            'end': (promo_end - datetime(1970, 1, 1)).total_seconds() if promo_end else None
        })
    return result


def get_promo_by_id(org_id, promo_id):
    promos = get_venue_promos(org_id)
    for promo in promos:
        if promo['id'] == promo_id:
            return promo


def get_order_promos(order, order_dict, set_info=False):
    order_request = order_dict

    url = '/orders/calculate_loyalty_discounts'
    payload = order_request
    company = CompanyNew.get_by_iiko_id(order.venue_id)
    result = json.loads(post_request(company, url, {}, payload, force_platius=True))
    logging.info(result)

    menu_list = list_menu(order.venue_id)

    # TODO gifts in LPQ are disabled!
    if order.venue_id == CompanyNew.HLEB:
        result['availableFreeProducts'] = []

    if result.get('availableFreeProducts'):
        for free_product in result['availableFreeProducts'][:]:
            product = get_product_from_menu(order.venue_id, product_code=free_product.get('productCode'),
                                            menu_list=menu_list)
            if product:
                free_product['id'] = product['productId']
                free_product['name'] = product['name']
                free_product['price'] = product['price']
                if not product['price'] and product.get('modifiers'):
                    free_product['price'] = product['modifiers'][0]['price']
                free_product['amount'] = 1
                free_product['sum'] = 0
                free_product['weight'] = product['weight']
                free_product['images'] = product['images']
                free_product['code'] = free_product['productCode']
            else:
                logging.error('not found product in menu')
                result['availableFreeProducts'].remove(free_product)

    if result.get('discountInfo'):
        for dis_info in result.get('discountInfo'):
            if dis_info.get('details'):
                for detail in dis_info.get('details'):
                    if detail.get('productCode'):
                        product = get_product_from_menu(order.venue_id, product_code=detail.get('productCode'),
                                                        menu_list=menu_list)
                        if product:
                            detail['id'] = product['productId'] if product.get('productId') else product.get('id')
                            detail['name'] = product['name']
                            detail['code'] = product['code']
                        else:
                            logging.error('product from iiko.biz not found!')
            if set_info:
                promo = get_promo_by_id(order.venue_id, dis_info.get('id'))
                dis_info['description'] = promo['description']
                dis_info['start'] = promo['start']
                dis_info['end'] = promo['end']
                dis_info['imageUrl'] = promo['imageUrl']

    return result
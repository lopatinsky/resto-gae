# coding=utf-8
import json
import logging
from datetime import datetime

from methods.iiko.base import get_request, post_request
from methods.iiko.menu import get_product_from_menu, list_menu, get_modifier_item
from models.iiko import CompanyNew

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

        def get_item(product_code):
            for item in order.items:
                if item['code'] == product_code:
                    return item
                if item.get('modifiers'):
                    for modifier in item.get('modifiers'):
                        if modifier.get('code') == product_code:
                            return item

        discount_sum = 0.0
        if promos.get('discountInfo'):
            for dis_info in promos.get('discountInfo'):
                if dis_info.get('details'):
                    for detail in dis_info.get('details'):
                        if detail.get('discountSum'):
                            item = get_item(detail.get('code'))
                            if not item:
                                logging.error('discounts not found!')
                                continue
                            if not item.get('discount_sum'):
                                item['discount_sum'] = detail['discountSum']
                                item['sum'] -= detail['discountSum']
                                cur_discount = detail['discountSum']
                            else:
                                if detail['discountSum'] > item['sum']:
                                    item['discount_sum'] += item['sum']
                                    cur_discount = item['sum']
                                    item['sum'] = 0
                                else:
                                    item['discount_sum'] += detail['discountSum']
                                    item['sum'] -= detail['discountSum']
                                    cur_discount = detail['discountSum']
                            discount_sum += cur_discount
        order.discount_sum = float(discount_sum)
        return add_bonus_to_payment(order_from_dict, discount_sum, True)


def add_bonus_to_payment(order, bonus_sum, is_deducted):

    def get_payment(order, name):
        for p_item in order['paymentItems']:
            if p_item['paymentType']['name'] == name:
                return p_item
        return None

    if order.get('paymentItems'):
        p_bonus = get_payment(order, 'iiko.Net')
        if p_bonus:
            p_bonus['sum'] += bonus_sum
            if is_deducted:
                get_payment(order, 'not iiko.Net')['sum'] -= bonus_sum
            return True
        else:
            return False
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
            result += mods_dict[mod['id']]['price'] * mod['amount']

    return result


def get_venue_promos(org_id):
    if org_id == CompanyNew.MIVAKO:
        from handlers.api.specials.mivako_promo import get_mivako_iiko_promos
        return get_mivako_iiko_promos()
    if org_id == CompanyNew.TYKANO:
        from handlers.api.specials.tykano_promos import get_tykano_iiko_promos
        return get_tykano_iiko_promos()

    url = '/organization/%s/marketing_campaigns' % org_id
    company = CompanyNew.get_by_iiko_id(org_id)
    promos = json.loads(get_request(company, url, {}))
    return [{
        'id': promo['id'],
        'name': promo['name'] if promo['name'] else '',
        'description': promo['description'] if promo['description'] else '',
        'image_url': promo['imageUrl'],
        'display_type': i % 4,
        'start': (datetime.strptime(promo['start'], '%Y-%m-%d') - datetime(1970, 1, 1)).total_seconds()
        if promo['start'] else None,
        'end': (datetime.strptime(promo['end'], '%Y-%m-%d') - datetime(1970, 1, 1)).total_seconds()
        if promo['end'] else None
    } for i, promo in enumerate(promos)]


def get_promo_by_id(org_id, promo_id):
    promos = get_venue_promos(org_id)
    for promo in promos:
        if promo['id'] == promo_id:
            return promo


def get_order_promos(order, order_dict, set_info=False):

    #order_request = prepare_order(order, customer, 1)
    order_request = order_dict
    order_request['organization'] = order.venue_id
    order_request['order']['fullSum'] = order.sum

    for item in order_request['order']['items']:
        product = get_product_from_menu(order.venue_id, product_id=item['id'])
        if not product:
            logging.error('product is not found in menu!')
            continue
        item['code'] = product['code']
        item['sum'] = product['price'] * item['amount']

        for m in item.get('modifiers', []):
            mod_item = get_modifier_item(order.venue_id, product_code=item['code'], order_mod_id=m.get('id'))
            m['code'] = mod_item.get('code')
            m['sum'] = mod_item.get('price', 0) * m.get('amount', 0) * item['amount']
            item['sum'] += m['sum']


    url = '/orders/calculate_loyalty_discounts'
    payload = order_request
    company = CompanyNew.get_by_iiko_id(order.venue_id)
    result = json.loads(post_request(company, url, {}, payload, force_platius=True))
    logging.info(result)

    if result.get('availableFreeProducts'):
        for free_product in result.get('availableFreeProducts'):
            product = get_product_from_menu(order.venue_id, product_code=free_product.get('productCode'))
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

    if result.get('discountInfo'):
        for dis_info in result.get('discountInfo'):
            if dis_info.get('details'):
                for detail in dis_info.get('details'):
                    if detail.get('productCode'):
                        product = get_product_from_menu(order.venue_id, product_code=detail.get('productCode'))
                        if product:
                            detail['id'] = product['productId'] if product.get('productId') else product.get('id')
                            detail['name'] = product['name']
                            detail['code'] = product['code']
                        else:
                            logging.error('product from iiko.biz not found!')
                        product = get_product_from_menu(order.venue_id, product_code=detail.get('productCode'))
                        detail['id'] = product['productId']
                        detail['name'] = product['name']
                        detail['code'] = product['code']
            if set_info:
                promo = get_promo_by_id(order.venue_id, dis_info.get('id'))
                dis_info['description'] = promo['description']
                dis_info['start'] = promo['start']
                dis_info['end'] = promo['end']
                dis_info['imageUrl'] = promo['imageUrl']

    return result
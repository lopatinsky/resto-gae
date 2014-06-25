# coding=utf-8
import datetime
import json
import logging
import urllib
from google.appengine.api import memcache, urlfetch
import model

__author__ = 'quiker'

IIKO_BASE_URL = 'https://iiko.net:9900/api/0'


def __get_request(api_path, params):
    url = '%s%s' % (IIKO_BASE_URL, api_path)
    if params:
        url = '%s?%s' % (url, urllib.urlencode(params))
    logging.info(url)
    return urlfetch.fetch(url, deadline=30, validate_certificate=False).content


def __post_request(api_path, params):
    url = '%s%s' % (IIKO_BASE_URL, api_path)
    payload = json.dumps(params)
    return urlfetch.fetch(url, method='POST', headers={'Content-Type': 'application/json'}, payload=payload, deadline=30, validate_certificate=False).content


def get_access_token():
    token = memcache.get('iiko_token')
    if not token:
        token = _fetch_access_token()
        memcache.set('iiko_token', token, time=10*60)
    return token


def _fetch_access_token():
    result = __get_request('/auth/access_token', {
        'user_id': 'Empatika',
        'user_secret': 'i33yMr7W17l0Ic3'
    })
    return result.strip('"')


def get_venues(token=None):
    venues = memcache.get('iiko_venues')
    if not venues:
        if not token:
            token = get_access_token()
        result = __get_request('/organization/list', {
            'access_token': token
        })
        obj = json.loads(result)
        venues = list()
        for v in obj:
            venues.append(model.Venue.venue_with_dict(v))
        memcache.set('iiko_venues', venues, time=30*60)
    return venues


def get_menu(venue_id, token=None):
    menu = memcache.get('iiko_menu_%s' % venue_id)
    if not menu:
        if not token:
            token = get_access_token()
        result = __get_request('/nomenclature/%s' % venue_id, {
            'access_token': token
        })
        obj = json.loads(result)
        product_by_categories = dict()
        for product in obj['products']:
            if product['parentGroup'] is None:
                continue
            if product.get('price', 0) == 0:
                continue
            lst = product_by_categories.get(product['parentGroup'])
            if not lst:
                lst = list()
                product_by_categories[product['parentGroup']] = lst
            lst.append({
                'price': product['price'],
                'name': product['name'].capitalize(),
                'productId': product['id'],
                'weight': product['weight'],
                'code': product['code']
            })

        categories = dict()
        for cat in obj['groups']:
            if not cat['isIncludedInMenu']:
                continue
            products = product_by_categories.get(cat['id'], [])
            categories[cat['id']] = {
                'id': cat['id'],
                'name': cat['name'].capitalize(),
                'products': products,
                'parent': cat['parentGroup'],
                'children': [],
                'hasChildren': False
            }

        for cat_id, cat in categories.items():
            cat_parent_id = cat.get('parent')
            if cat_parent_id:
                parent = categories[cat_parent_id]
                parent['children'].append(cat)
                parent['hasChildren'] = True
                if parent.get('products'):
                    parent['products'] = []

        for cat_id, cat in categories.items():
            cat_parent_id = cat.get('parent')
            if cat_parent_id:
                del categories[cat_id]

        menu = [cat[1] for cat in categories.items()]
        memcache.set('iiko_menu_%s' % venue_id, menu, time=1*3600)
    return menu


def place_order(order, customer):
    obj = {
        'restaurantId': order.venue_id,
        'deliveryTerminalId': 'dd121a59-a43e-0690-0144-f47bced50158',
        'customer': {
            'name': customer.name,
            'phone': customer.phone,
            'id': customer.customer_id
        },
        'order': {
            'date': order.date.strftime('%Y-%m-%d %H:%M:%S'),
            'isSelfService': '1',
            'paymentItems': {
                'paymentType': {
                    'id': 'bf2fd2db-cc75-46fa-97af-4f9dc68bb34b',
                    'code': 333,
                    'name': u'Банковские карты'
                },
                'sum': order.sum,
                'isProcessedExternally': 1
            },
            'phone': customer.phone,
            'items': order.items
        }
    }
    if order.is_delivery:
        obj['order']['address'] = order.address
    result = __post_request('/orders/add?request_timeout=30&access_token=%s' % get_access_token(), obj)
    logging.info(result)
    return json.loads(result)


def order_info(order):
    result = __get_request('/orders/info', {
        'access_token': get_access_token(),
        'organization': order.venue_id,
        'order': order.order_id,
        'request_timeout': '30'
    })
    return json.loads(result)


def order_info1(order_id, venue_id):
    result = __get_request('/orders/info', {
        'access_token': get_access_token(),
        'organization': venue_id,
        'order': order_id,
        'request_timeout': '30'
    })
    return json.loads(result)

def get_history(client_id,venue_id,token=None):
    if not token:
        token = get_access_token()
    result = __get_request('/orders/deliveryHistory', {
        'access_token': token,
        'organization': venue_id,
        'customer': client_id

    })
    obj= json.loads(result)
    return obj

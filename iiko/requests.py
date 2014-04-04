import json
import logging
import urllib
from google.appengine.api import memcache, urlfetch
import model

__author__ = 'quiker'

IIKO_BASE_URL = 'https://iiko.net:9900/api/0'


def __make_request(api_path, params):
    url = '%s%s' % (IIKO_BASE_URL, api_path)
    if params:
        url = '%s?%s' % (url, urllib.urlencode(params))
    logging.info(url)
    return urlfetch.fetch(url, deadline=30, validate_certificate=False).content


def get_access_token():
    token = memcache.get('iiko_token')
    if not token:
        token = _fetch_access_token()
        memcache.set('iiko_token', token, time=10*60)
    return token


def _fetch_access_token():
    result = __make_request('/auth/access_token', {
        'user_id': 'Empatika',
        'user_secret': 'i33yMr7W17l0Ic3'
    })
    return result.strip('"')


def get_venues(token=None):
    venues = memcache.get('iiko_venues')
    if not venues:
        if not token:
            token = get_access_token()
        result = __make_request('/organization/list', {
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
        result = __make_request('/nomenclature/%s' % venue_id, {
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
        memcache.set('iiko_menu_%s' % venue_id, menu)
    return menu
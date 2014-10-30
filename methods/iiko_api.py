# coding=utf-8
from datetime import datetime, timedelta
import json
import logging
import urllib
import operator

from google.appengine.api import memcache, urlfetch
import webapp2

from models.iiko import Venue, Company, PaymentType
from methods.image_cache import convert_url


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
    logging.info("PAYLOAD %s" % str(payload))
    logging.info(url)

    return urlfetch.fetch(url, method='POST', headers={'Content-Type': 'application/json'}, payload=payload, deadline=30,
                          validate_certificate=False).content


def get_access_token(org_id):
    token = memcache.get('iiko_token_%s' % org_id)
    if not token:
        token = _fetch_access_token(org_id)
        memcache.set('iiko_token_%s' % org_id, token, time=10*60)
    return token


def get_organization_token(org_id):
    memcache.set('iiko_company_%s' % org_id, org_id, time=24*3600)


def _fetch_access_token(org_id):
    organisation_id = memcache.get('iiko_company_%s' % org_id)
    if not organisation_id:
        get_organization_token(organisation_id)
    company = Company.get_by_id(int(org_id))
    result = __get_request('/auth/access_token', {
        'user_id': company.name,  # 'Empatika'
        'user_secret': company.password  # 'i33yMr7W17l0Ic3'
    })
    return result.strip('"')


def get_venues(org_id, token=None):
    venues = memcache.get('iiko_venues_%s' % org_id)
    if not venues:
        if not token:
            token = get_access_token(org_id)
        result = __get_request('/organization/list', {
            'access_token': token
        })
        logging.info(result)
        obj = json.loads(result)
        venues = list()
        for v in obj:
            if v['id'] == "23f9ce79-2dd3-11e4-80c8-0025907e32e9":
                continue  # TODO demostand_empatika
            venues.append(Venue.venue_with_dict(v, org_id))
        memcache.set('iiko_venues_%s' % org_id, venues, time=30*60)
    return venues


def get_all_items_in_modifier(result, modif_id, min_amount):
    res = []
    name = ''
    group_id = ''
    for item in result['products']:
        if item['groupId']:
            if item['groupId'] == modif_id and min_amount != 0:
                res.append({
                    'id': item['id'],
                    'name': item['name'],
                    'amount': min_amount,
                })

    for item in result['groups']:
        if item['id'] == modif_id:
            name = item['name']
            group_id = item['id']
            break
    return {
        'items': res,
        'name': name,
        'groupId': group_id
    }


def get_stop_list(venue_id):
    org_id = Venue.venue_by_id(venue_id).company_id
    result = __get_request('/stopLists/getDeliveryStopList', {
        'access_token': get_access_token(org_id),
        'organization': venue_id,
    })
    return json.loads(result)


def create_order_with_bonus(venue_id, order):
    org_id = Venue.venue_by_id(venue_id).company_id
    result = __post_request('/orders/create_order?access_token=%s&request_timeout=30&organization=%s' %
                            (get_access_token(org_id), venue_id), order)
    return result


def get_orders_with_payments(venue_id):
    org_id = Venue.venue_by_id(venue_id).company_id
    result = __get_request('/orders/get_orders_with_payments', {
        'access_token': get_access_token(org_id),
        'organization': venue_id,
        'from': datetime.fromtimestamp(1406550552)  # TODO: timestamp
    })
    return json.loads(result)


def update_bonus_order(venue_id, order):
    org_id = Venue.venue_by_id(venue_id).company_id
    result = __post_request('/orders/update_order/access_token=%s&request_timeout=30&organization=%s' %
                            (get_access_token(org_id), venue_id), order)
    return json.loads(result)


def get_iiko_net_payments(venue_id, order_id):
    org_id = Venue.venue_by_id(venue_id).company_id
    result = __get_request('/orders/get_iiko_net_payment', {
        'access_token': get_access_token(org_id),
        'organization': venue_id,
        'order_id': order_id
    })
    return json.loads(result)


def pay_order(venue_id, payment_sum, order):
    org_id = Venue.venue_by_id(venue_id).company_id
    result = __post_request('/orders/pay_order/access_token=%s&'
                            'request_timeout=30&organization=%s&payment_sum=%d' %
                            (get_access_token(org_id), venue_id, payment_sum), order)
    return json.loads(result)


def confirm_order(venue_id, sum_for_bonus, order_id):
    org_id = Venue.venue_by_id(venue_id).company_id
    result = __get_request('/orders/confirm_order', {
        'access_token': get_access_token(org_id),
        'organization': venue_id,
        'order_id': order_id,
        'sum_for_bonus': sum_for_bonus
    })
    return json.loads(result)


def abort_order(venue_id, order_id):
    org_id = Venue.venue_by_id(venue_id).company_id
    result = __get_request('/orders/abort_order', {
        'access_token': get_access_token(org_id),
        'organization': venue_id,
        'order_id': order_id,
    })
    return json.loads(result)


def get_menu(venue_id, token=None):
    menu = memcache.get('iiko_menu_%s' % venue_id)
    org_id = Venue.venue_by_id(venue_id).company_id
    if not menu:
        if not token:
            token = get_access_token(org_id)
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
            grp_modifiers = list()
            if product['groupModifiers']:
                for modif in product['groupModifiers']:
                    items = get_all_items_in_modifier(obj, modif['modifierId'], modif['minAmount'])
                    if items['items']:
                        grp_modifiers.append(items)
            lst.append({
                'price': product['price'],
                'name': product['name'].capitalize(),
                'productId': product['id'],
                'order': product['order'],
                'weight': product['weight'],
                'carbohydrateAmount': product['carbohydrateAmount'],
                'energyAmount': product['energyAmount'],
                'fatAmount': product['fatAmount'],
                'fiberAmount': product['fiberAmount'],
                'code': product['code'],
                'images': [convert_url(webapp2.get_request(), img['imageUrl']) for img in product.get('images', [])],
                'description': product['description'],
                'modifiers': grp_modifiers
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
                'hasChildren': False,
                'image': cat['images'],
                'order': cat['order']
            }
            for image in categories[cat['id']]['image']:
                image['imageUrl'] = convert_url(webapp2.get_request(), image['imageUrl'])

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

        for cat_id, cat in categories.items():
            children = cat.get('children')
            if children:
                cat['children'] = sorted(children, key=operator.itemgetter('order'), reverse=True)

        menu = [cat[1] for cat in categories.items()]
        memcache.set('iiko_menu_%s' % venue_id, menu, time=1*3600)
    return sorted(menu, key=operator.itemgetter('order'), reverse=True)


def check_food(venue_id, items):
    stop_list = get_stop_list(venue_id)
    for item in stop_list['stopList'][0]['items']:
        if item['productId'] in [x['id'] for x in items]:
            return True
    return False


def place_order(order, customer, payment_type):
    venue = Venue.venue_by_id(order.venue_id)
    local_date = order.date + timedelta(seconds=venue.get_timezone_offset())

    obj = {
        'restaurantId': order.venue_id,
        #TODO terminal id
        'deliveryTerminalId': '2ecfd7dd-19e8-c7f4-0147-ec886f9c2aa1',
        'customer': {
            'name': customer.name,
            'phone': customer.phone,
        },
        'order': {
            'date': local_date.strftime('%Y-%m-%d %H:%M:%S'),
            'isSelfService': 0 if order.is_delivery else 1,
            'paymentItems': [{
                'paymentType': {
                    'code': '',
                },
                'sum': order.sum,
                'isProcessedExternally': 0
            }],
            'phone': customer.phone,
            'items': order.items,
            'comment': order.comment
        }
    }

    customer_id = customer.customer_id
    if customer_id:
        obj['customer']['id'] = customer_id
    if order.is_delivery:
        obj['order']['address'] = order.address

    typ = PaymentType.get_by_type_id(payment_type)
    if typ.type_id == 1:
        obj['order']['paymentItems'][0]['paymentType']['code'] = typ.iiko_uuid
    elif typ.type_id == 2:
        obj['order']['paymentItems'][0]['paymentType']['code'] = typ.iiko_uuid
        obj['order']['paymentItems'][0]['isProcessedExternally'] = 1
    elif typ.type_id == 3:
        obj['order']['paymentItems'][0]['paymentType']['code'] = typ.iiko_uuid

    org_id = venue.company_id
    if org_id == 5717119551406080 or org_id == 5700553057239040:
        del obj['order']['paymentItems']
        del obj['deliveryTerminalId']

    # print create_order_with_bonus(order.venue_id, obj)
    logging.info("OBJECT %s" % str(json.dumps(obj)))
    pre_check = __post_request('/orders/checkCreate?access_token=%s&requestTimeout=30' % get_access_token(org_id), obj)
    logging.info(pre_check)
    # pre_check_obj = json.loads(pre_check)
    # if pre_check_obj['code']:
    #     return json.loads({
    #         'code': pre_check_obj['code'],
    #         'description': pre_check_obj['description']
    #     })

    result = __post_request('/orders/add?requestTimeout=30&access_token=%s' % get_access_token(org_id), obj)
    logging.info(result)
    return json.loads(result)


def order_info(order):
    org_id = Venue.venue_by_id(order.venue_id).company_id
    result = __get_request('/orders/info', {
        'access_token': get_access_token(org_id),
        'organization': order.venue_id,
        'order': order.order_id
    })
    return json.loads(result)


def order_info1(order_id, venue_id):
    org_id = Venue.venue_by_id(venue_id).company_id
    result = __get_request('/orders/info', {
        'access_token': get_access_token(org_id),
        'organization': venue_id,
        'order': order_id
    })
    logging.info(result)
    return json.loads(result)


def get_history(client_id, venue_id, token=None):
    org_id = Venue.venue_by_id(venue_id).company_id
    if not token:
        token = get_access_token(org_id)
    result = __get_request('/orders/deliveryHistory', {
        'access_token': token,
        'organization': venue_id,
        'customer': client_id
    })
    obj = json.loads(result)
    return obj


def get_new_orders(venue_id, start_date, end_date, token=None):
    venue = Venue.venue_by_id(venue_id)
    offset = timedelta(seconds=venue.get_timezone_offset())
    if not start_date:
        start_date = datetime(2000, 1, 1, 0, 0, 0)
    start_date += offset
    if not end_date:
        end_date = datetime.now()
    end_date += offset

    if not token:
        token = get_access_token(venue.company_id)
    result = __get_request('/orders/deliveryOrders', {
        'access_token': token,
        'organization': venue_id,
        'dateFrom': start_date.strftime('%Y-%m-%d %H:%M:%S'),
        'dateTo': end_date.strftime('%Y-%m-%d %H:%M:%S'),
        'deliveryStatus': 'UNCONFIRMED'
    })
    obj = json.loads(result)
    return obj


def get_payment_types(venue_id, token=None):
    org_id = Venue.venue_by_id(venue_id).company_id
    if not token:
        token = get_access_token(org_id)
    result = __get_request('/paymentTypes/getPaymentTypes', {
        'access_token': token,
        'organization': venue_id
    })
    obj = json.loads(result)
    return obj


def get_delivery_restrictions(venue_id, token=None):
    org_id = Venue.venue_by_id(venue_id).company_id
    if not token:
        token = get_access_token(org_id)
    result = __get_request('/deliverySettings/getDeliveryRestrictions', {
        'access_token': token,
        'organization': venue_id,
    })
    return json.loads(result)
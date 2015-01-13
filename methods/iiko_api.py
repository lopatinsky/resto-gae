# coding=utf-8
from collections import defaultdict
from datetime import datetime, timedelta
import json
import logging
import urllib
import operator
from models import iiko
from collections import deque

from google.appengine.api import memcache, urlfetch
import webapp2

from models.iiko import Venue, Company
from methods.image_cache import convert_url


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

    return urlfetch.fetch(url, method='POST', headers={'Content-Type': 'application/json'}, payload=payload,
                          deadline=30, validate_certificate=False).content


def get_access_token(org_id):
    token = memcache.get('iiko_token_%s' % org_id)
    if not token:
        token = _fetch_access_token(org_id)
        memcache.set('iiko_token_%s' % org_id, token, time=10*60)
    return token


def _fetch_access_token(org_id):
    logging.info(org_id)
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
            venues.append(Venue.venue_with_dict(v, org_id))
        memcache.set('iiko_venues_%s' % org_id, venues, time=30*60)
    return venues


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


def _get_menu_modifiers(menu):
    group_modifiers = defaultdict(lambda: {'items': []})
    modifiers = {}
    for p in menu['products']:
        if p['type'] == 'modifier':
            mod_info = {
                'id': p['id'],
                'name': p['name'],
                'price': p['price']
            }
            modifiers[p['id']] = mod_info
            if p['groupId']:
                group_mod_info = dict(mod_info, groupId=p['groupId'])
                group_modifiers[p['groupId']]['items'].append(group_mod_info)
    for g in menu['groups']:
        if g['id'] in group_modifiers:
            group_modifiers[g['id']].update({
                'groupId': g['id'],
                'name': g['name'],
            })
    return group_modifiers, modifiers


def _clone(d):
    return json.loads(json.dumps(d))


def _load_menu(venue, token=None):
    org_id = venue.company_id
    if not token:
        token = get_access_token(org_id)
    result = __get_request('/nomenclature/%s' % venue.venue_id, {
        'access_token': token
    })
    iiko_menu = json.loads(result)
    group_modifiers, modifiers = _get_menu_modifiers(iiko_menu)
    category_products = defaultdict(list)
    for product in iiko_menu['products']:
        if product['parentGroup'] is None:
            continue

        single_modifiers = []
        for m in product['modifiers']:
            modifier = _clone(modifiers[m['modifierId']])
            modifier['minAmount'] = m['minAmount']
            modifier['maxAmount'] = m['maxAmount']
            modifier['defaultAmount'] = m['defaultAmount']
            single_modifiers.append(modifier)

        grp_modifiers = []
        for m in product['groupModifiers']:
            group = _clone(group_modifiers[m['modifierId']])
            group['minAmount'] = m['minAmount']
            group['maxAmount'] = m['maxAmount']
            for item in group['items']:
                item['amount'] = m['minAmount']  # TODO legacy
            grp_modifiers.append(group)

        add_info_str = product['additionalInfo']
        add_info = None
        if add_info_str:
            try:
                add_info = json.loads(product['additionalInfo'])
            except ValueError:
                add_info_str = None  # don't pass through raw info if cannot parse JSON

        category_products[product['parentGroup']].append({
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
            'images': [convert_url(webapp2.get_request(), img['imageUrl'])
                       for img in product.get('images', [])
                       if img['imageUrl']][::-1],
            'description': product['description'],
            'additionalInfo': add_info,
            'additionalInfo1': add_info_str,
            'single_modifiers': single_modifiers,
            'modifiers': grp_modifiers
        })

    categories = dict()
    for cat in iiko_menu['groups']:
        if not cat['isIncludedInMenu']:
            continue
        products = category_products[cat['id']]
        categories[cat['id']] = {
            'id': cat['id'],
            'name': cat['name'].capitalize(),
            'products': products,
            'parent': cat['parentGroup'],
            'children': [],
            'hasChildren': False,
            'image': [image for image in cat['images'] if image['imageUrl']][::-1],
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

    return sorted(categories.values(), key=operator.itemgetter('order'), reverse=True)


def _filter_menu(menu):
    def process_category(category):
        category['products'] = [p
                                for p in category['products']
                                if p['price'] > 0 or p['single_modifiers'] or p['modifiers']]
        for sub in category['children']:
            process_category(sub)
        category['children'] = [c
                                for c in category['children']
                                if c['products'] or c['children']]

    for root_category in menu:
        process_category(root_category)

    menu[:] = [c
               for c in menu
               if c['products'] or c['children']]


def get_menu(venue_id, force_reload=False, token=None, filtered=True):
    menu = memcache.get('iiko_menu_%s' % venue_id)
    if not menu or force_reload:
        venue = Venue.venue_by_id(venue_id)
        if not venue.menu or force_reload:
            venue.menu = _load_menu(venue, token)
            venue.put()
        menu = venue.menu
        memcache.set('iiko_menu_%s' % venue_id, menu, time=1*3600)
    if filtered:
        _filter_menu(menu)
    return menu


def check_food(venue_id, items):
    stop_list = get_stop_list(venue_id)
    for item in stop_list['stopList'][0]['items']:
        if item['productId'] in [x['id'] for x in items]:
            return True
    return False


def set_discounts(order, order_from_dict, token=None):

        def get_item(product_id):
            for item in order.items:
                if item['id'] == product_id:
                    return item
                if item.get('modifiers'):
                    for modifier in item.get('modifiers'):
                        if modifier.get('items'):
                            for m_item in modifier.get('items'):
                                if m_item.get('id') == product_id:
                                    return item

        if not token:
            token = get_access_token(Venue.venue_by_id(order.venue_id).company_id)

        promos = get_order_promos(order, token=token)
        if promos.get('availableFreeProducts'):
            for gift in promos.get('availableFreeProducts'):
                gift['sum'] = 0
                order.items.append(gift)

        discount_sum = 0
        if promos.get('discountInfo'):
            for dis_info in promos.get('discountInfo'):
                if dis_info.get('details'):
                    for detail in dis_info.get('details'):
                        if detail.get('discountSum'):
                            item = get_item(detail.get('id'))
                            if not item.get('discount_sum'):
                                item['discount_sum'] = detail['discountSum']
                            else:
                                item['discount_sum'] += detail['discountSum']
                            item['sum'] -= detail['discountSum']
                            discount_sum += item['discount_sum']
        order.discount_sum = discount_sum
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


def prepare_order(order, customer, payment_type):
    venue = Venue.venue_by_id(order.venue_id)
    local_date = order.date + timedelta(seconds=venue.get_timezone_offset())
    additional_data = '{"externalIdType": "PHONE", "externalId": "'
    additional_data += customer.phone
    additional_data += '"}'
    obj = {
        'restaurantId': order.venue_id,
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
                    'name': 'not iiko.Net'
                },
                'sum': order.sum,
                "combinatable": True,
                'isProcessedExternally': 0
            },
            {
                "sum": 0.0,
                'paymentType': {
                    "code": "INET",
                    "name": "iiko.Net",
                    "comment": "",
                    "combinatable": True,
                },
                "additionalData": additional_data,
                "isProcessedExternally": False,
                "isPreliminary": True,
                "isExternal": True,
            }
            ],
            'phone': customer.phone,
            'items': order.items,
            'comment': order.comment,
            'address': {
                'home': 0
            }
        }
    }

    if not order.is_delivery:
        obj['deliveryTerminalId'] = get_delivery_terminal_id(order.venue_id)

    customer_id = customer.customer_id
    if customer_id:
        obj['customer']['id'] = customer_id
    if order.is_delivery:
        obj['order']['address'] = order.address

    if payment_type:
        typ = venue.get_payment_type(payment_type)
        obj['order']['paymentItems'][0]['paymentType']['code'] = typ.iiko_uuid
        if typ.type_id == 2:
            obj['order']['paymentItems'][0].update({
                'isProcessedExternally': True,
                'isExternal': True,
                'isPreliminary': True
            })

    return obj


def pre_check_order(company_id, order_dict):
    token = get_access_token(company_id)
    pre_check = __post_request('/orders/checkCreate?access_token=%s&requestTimeout=30' % token, order_dict)
    logging.info(pre_check)
    return json.loads(pre_check)


def place_order(company_id, order_dict):
    token = get_access_token(company_id)
    result = __post_request('/orders/add?requestTimeout=30&access_token=%s' % token, order_dict)
    logging.info(result)
    return json.loads(result)


def order_info(order):
    org_id = Venue.venue_by_id(order.venue_id).company_id
    result = __get_request('/orders/info', {
        'requestTimeout': 30,
        'access_token': get_access_token(org_id),
        'organization': order.venue_id,
        'order': order.order_id
    })
    return json.loads(result)


def order_info1(order_id, venue_id):
    org_id = Venue.venue_by_id(venue_id).company_id
    result = __get_request('/orders/info', {
        'requestTimeout': 30,
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


def get_venue_promos(venue_id, token=None):
    if not token:
        token = get_access_token(Venue.venue_by_id(venue_id).company_id)
    url = '/organization/%s/marketing_campaigns' % venue_id
    payload = {
        'access_token': token
    }
    result = __get_request(url, payload)
    return json.loads(result)


def list_menu(venue_id, token=None):

    def get_categories(cat_parent):
        result_c = []
        for other_cat in cat_parent['children']:
            result_c.append(other_cat)
        return result_c

    def get_products(cat_dict):
        result_p = []
        for product in cat_dict['products']:
            result_p.append(product)
        return result_p

    menu = get_menu(venue_id, False, token, False)
    queue = deque(menu)
    products = []
    while len(queue):
        cat = queue.popleft()
        if not cat['hasChildren']:
            products.extend(get_products(cat))
        else:
            queue.extend(get_categories(cat))

    return products


def get_product_from_menu(venue_id, token=None, product_code=None, product_id=None):
    menu = list_menu(venue_id, token)
    for product in menu:
        if product['productId'] == product_id or product['code'] == product_code:
            return product


def get_group_modifier(venue_id, group_id, modifier_id, token=None):
    menu = get_menu(venue_id, False, token, False)
    group_modifiers, modifiers = _get_menu_modifiers(menu)
    items = group_modifiers[group_id]['items']
    for item in items:
        if item['id'] == modifier_id:
            return item


def get_promo_by_id(venue_id, promo_id, token=None):
    if not token:
        token = get_access_token(Venue.venue_by_id(venue_id).company_id)
    promos = get_venue_promos(venue_id, token)
    for promo in promos:
        if promo['id'] == promo_id:
            return promo


def get_order_promos(order, token=None):
    if not token:
        token = get_access_token(Venue.venue_by_id(order.venue_id).company_id)
    order_request = prepare_order(order, order.customer.get(), 1)
    order_request['organization'] = order.venue_id
    order_request['order']['fullSum'] = order.sum

    for item in order_request['order']['items']:
        product = get_product_from_menu(order.venue_id, product_id=item['id'])
        item['code'] = product['code']
        item['sum'] = product['price'] * item['amount']
        if item['sum'] == 0:
            if item['modifiers']:
                item['sum'] = sum(get_group_modifier(order.venue_id, m['groupId'], m['id']) * m['amount']
                                  for m in item.get('modifiers'))

    url = '/orders/calculate_loyalty_discounts?access_token=%s' % token
    payload = order_request
    result = json.loads(__post_request(url, payload))

    if result.get('availableFreeProducts'):
        for free_product in result.get('availableFreeProducts'):
            product = get_product_from_menu(order.venue_id, product_code=free_product.get('productCode'))
            free_product['id'] = product['productId']
            free_product['name'] = product['name']
            free_product['amount'] = 1
            free_product['code'] = free_product['productCode']

    if result.get('discountInfo'):
        for dis_info in result.get('discountInfo'):
            if dis_info.get('details'):
                for detail in dis_info.get('details'):
                    if detail.get('productCode'):
                        product = get_product_from_menu(order.venue_id, product_code=detail.get('productCode'))
                        detail['id'] = product['productId']
                        detail['name'] = product['name']
                        detail['code'] = product['code']
            promo = get_promo_by_id(order.venue_id, dis_info.get('id'), token)
            dis_info['description'] = promo['description']
            dis_info['start'] = promo['start']
            dis_info['end'] = promo['end']
            dis_info['imageUrl'] = promo['imageUrl']

    return result


def get_delivery_terminal_id(venue_id, token=None):
    memcache_key = "deliveryTerminalId_%s" % venue_id
    dt_id = memcache.get(memcache_key)
    if not dt_id:
        if not token:
            org_id = Venue.venue_by_id(venue_id).company_id
            token = get_access_token(org_id)
        response = __get_request('/deliverySettings/getDeliveryTerminals', {
            'access_token': token,
            'organization': venue_id
        })
        result = json.loads(response)
        terminals = result['deliveryTerminals']
        if terminals:
            dt_id = terminals[0]['deliveryTerminalId']
            memcache.set(memcache_key, dt_id, time=24*3600)
    return dt_id


def create_or_update_customer(customer, venue_id, token=None):
    if not token:
        token = get_access_token(Venue.venue_by_id(venue_id).company_id)
    url = '/customers/create_or_update?access_token=%s&organization=%s' % (token, venue_id)
    params = {
        'customer': {
            'phone': customer.phone,
            'name': customer.name
        }
    }
    result = __post_request(url, params)
    if result:
        return result
    else:
        return 'failure'
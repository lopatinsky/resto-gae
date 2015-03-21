# coding=utf-8
from collections import defaultdict
from datetime import datetime, timedelta
import json
import logging
import urllib
import operator
from collections import deque

from google.appengine.api import memcache, urlfetch
import webapp2

from models.iiko import Venue, Company
from methods.image_cache import convert_url


IIKO_BASE_URL = 'http://54.69.38.101/iikonet'


def __get_request(company_id, api_path, params):
    def do():
        url = '%s%s' % (IIKO_BASE_URL, api_path)
        if params:
            url = '%s?%s' % (url, urllib.urlencode(params))
        logging.info(url)
        return urlfetch.fetch(url, deadline=30, validate_certificate=False)

    params['access_token'] = get_access_token(company_id)
    result = do()
    if result.status_code == 401:
        logging.warning("bad token")
        params['access_token'] = get_access_token(company_id, refresh=True)
        result = do()
    return result.content


def __post_request(company_id, api_path, params, payload):
    def do():
        url = '%s%s' % (IIKO_BASE_URL, api_path)
        if params:
            url = '%s?%s' % (url, urllib.urlencode(params))
        json_payload = json.dumps(payload)
        logging.info("PAYLOAD %s" % str(json_payload))
        logging.info(url)

        return urlfetch.fetch(url, method='POST', headers={'Content-Type': 'application/json'}, payload=json_payload,
                              deadline=30, validate_certificate=False)

    params['access_token'] = get_access_token(company_id)
    result = do()
    if result.status_code == 401:
        logging.warning("bad token")
        params['access_token'] = get_access_token(company_id, refresh=True)
        result = do()
    return result.content


def get_access_token(org_id, refresh=False):
    token = memcache.get('iiko_token_%s' % org_id)
    if not token or refresh:
        token = _fetch_access_token(org_id)
        memcache.set('iiko_token_%s' % org_id, token, time=10*60)
    return token


def _fetch_access_token(org_id):
    company = Company.get_by_id(int(org_id))
    result = urlfetch.fetch(
        IIKO_BASE_URL + '/auth/access_token?user_id=%s&user_secret=%s' % (company.name, company.password),
        deadline=10, validate_certificate=False)
    return result.content.strip('"')


def get_venues(org_id):
    venues = memcache.get('iiko_venues_%s' % org_id)
    if not venues:
        result = __get_request(org_id, '/organization/list', {})
        logging.info(result)
        obj = json.loads(result)
        if not isinstance(obj, list):
            return []
        logging.info(obj)
        venues = list()
        for v in obj:
            venues.append(Venue.venue_with_dict(v, org_id))
        memcache.set('iiko_venues_%s' % org_id, venues, time=30*60)
    return venues


def get_stop_list(venue_id):
    org_id = Venue.venue_by_id(venue_id).company_id
    result = __get_request(org_id, '/stopLists/getDeliveryStopList', {
        'organization': venue_id,
    })
    return json.loads(result)


def get_orders_with_payments(venue_id):
    org_id = Venue.venue_by_id(venue_id).company_id
    result = __get_request(org_id, '/orders/get_orders_with_payments', {
        'organization': venue_id,
        'from': datetime.fromtimestamp(1406550552)  # TODO: timestamp
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
                'price': p['price'],
                'code': p['code']
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


def _load_menu(venue):
    org_id = venue.company_id
    result = __get_request(org_id, '/nomenclature/%s' % venue.venue_id, {})
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
            'description': product['description'] or '',
            'additionalInfo': add_info,
            'additionalInfo1': add_info_str,
            'single_modifiers': single_modifiers,
            'modifiers': grp_modifiers
        })

    categories = dict()
    for cat in iiko_menu['groups']:
        # TODO beer in sushilar
        if venue.venue_id == Venue.SUSHILAR and cat['id'] == '6e4b8c9c-df45-40f6-8356-ac8039e3f630':
            continue
        if not cat['isIncludedInMenu']:
            continue
        products = sorted(category_products[cat['id']], key=operator.itemgetter('order'))
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
        # todo hack for sushilar
        if cat['id'] == '170f94fd-3adb-4bb5-bd14-836bd81d2172':
            categories['170f94fd-3adb-4bb5-bd14-836bd81d2172']['image'].append({
                'imageUrl': 'http://empatika-resto-test.appspot.com/static/img/sushilar_spicy_rolls.png'
            })

    for cat_id, cat in categories.items():
        cat_parent_id = cat.get('parent')
        if cat_parent_id == cat_id:
            cat['parent'] = cat_parent_id = None
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
            cat['children'] = sorted(children, key=operator.itemgetter('order'))

    return sorted(categories.values(), key=operator.itemgetter('order'))


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


def get_menu(venue_id, force_reload=False, filtered=True):
    menu = memcache.get('iiko_menu_%s' % venue_id)
    if not menu or force_reload:
        venue = Venue.venue_by_id(venue_id)
        if not venue.menu or force_reload:
            venue.menu = _load_menu(venue)
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
        order.sum += gift['price'] * gift['amount']
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


def prepare_order(order, customer, payment_type):
    venue = Venue.venue_by_id(order.venue_id)
    company = Company.get_by_id(venue.company_id)
    local_date = order.date + timedelta(seconds=venue.get_timezone_offset())
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
            }],
            'phone': customer.phone,
            'items': order.items,
            'comment': order.comment,
            'address': {
                'home': 0
            }
        }
    }

    if company.is_iiko_system:
        obj['order']['paymentItems'].append({
            "sum": 0.0,
            'paymentType': {
                "code": "INET",
                "name": "iiko.Net",
                "comment": "",
                "combinatable": True,
            },
            "additionalData": json.dumps({
                "externalIdType": "PHONE",
                "externalId": customer.phone
            }),
            "isProcessedExternally": False,
            "isPreliminary": True,
            "isExternal": True,
        })

    if customer.customer_id:
        obj['customer']['id'] = customer.customer_id

    if not order.is_delivery:
        obj['deliveryTerminalId'] = get_delivery_terminal_id(order.venue_id)
    elif order.venue_id == Venue.ORANGE_EXPRESS:
        dt_mapping = {
            u"Одинцово": "2b20fde1-727f-e430-013e-203bb2e09905",
            u"Егорьевск": "2b20fde1-727f-e430-013e-203bb2e09af1",
            u"Подольск": "e0a67a59-c018-2c9c-0149-893d7b97148e",
            u"Климовск": "e0a67a59-c018-2c9c-0149-893d7b97148e",
            u"Домодедово": "2d163ab4-ce5d-e5cf-014b-84e547cfdf79"
        }
        obj['deliveryTerminalId'] = dt_mapping[order.address['city']]

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
    pre_check = __post_request(company_id, '/orders/checkCreate', {
        'requestTimeout': 30
    }, order_dict)
    logging.info(pre_check)
    return json.loads(pre_check)


def place_order(company_id, order_dict):
    result = __post_request(company_id, '/orders/add', {
        'requestTimeout': 30
    }, order_dict)
    logging.info(result)
    return json.loads(result)


def order_info(order):
    org_id = Venue.venue_by_id(order.venue_id).company_id
    result = __get_request(org_id, '/orders/info', {
        'requestTimeout': 30,
        'organization': order.venue_id,
        'order': order.order_id
    })
    return json.loads(result)


def order_info1(order_id, venue_id):
    org_id = Venue.venue_by_id(venue_id).company_id
    result = __get_request(org_id, '/orders/info', {
        'requestTimeout': 30,
        'organization': venue_id,
        'order': order_id
    })
    logging.info(result)
    return json.loads(result)


def get_history(client_id, venue_id):
    org_id = Venue.venue_by_id(venue_id).company_id
    result = __get_request(org_id, '/orders/deliveryHistory', {
        'organization': venue_id,
        'customer': client_id,
        'requestTimeout': 20
    })
    obj = json.loads(result)
    return obj


def get_new_orders(venue_id, start_date, end_date):
    venue = Venue.venue_by_id(venue_id)
    offset = timedelta(seconds=venue.get_timezone_offset())
    if not start_date:
        start_date = datetime(2000, 1, 1, 0, 0, 0)
    start_date += offset
    if not end_date:
        end_date = datetime.now()
    end_date += offset

    result = __get_request(venue.company_id, '/orders/deliveryOrders', {
        'organization': venue_id,
        'dateFrom': start_date.strftime('%Y-%m-%d %H:%M:%S'),
        'dateTo': end_date.strftime('%Y-%m-%d %H:%M:%S'),
    })
    obj = json.loads(result)
    return obj


def get_payment_types(venue_id):
    org_id = Venue.venue_by_id(venue_id).company_id
    result = __get_request(org_id, '/paymentTypes/getPaymentTypes', {
        'organization': venue_id
    })
    obj = json.loads(result)
    return obj


def get_delivery_restrictions(venue_id):
    org_id = Venue.venue_by_id(venue_id).company_id
    result = __get_request(org_id, '/deliverySettings/getDeliveryRestrictions', {
        'organization': venue_id,
    })
    return json.loads(result)


def get_venue_promos(venue_id):
    url = '/organization/%s/marketing_campaigns' % venue_id
    company_id = Venue.venue_by_id(venue_id).company_id
    promos = json.loads(__get_request(company_id, url, {}))
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


def list_menu(venue_id):

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

    menu = get_menu(venue_id, filtered=False)
    queue = deque(menu)
    products = []
    while len(queue):
        cat = queue.popleft()
        if not cat['hasChildren']:
            products.extend(get_products(cat))
        else:
            queue.extend(get_categories(cat))

    return products


def get_product_from_menu(venue_id, product_code=None, product_id=None):
    menu = list_menu(venue_id)
    for product in menu:
        if product['productId'] == product_id or product['code'] == product_code:
            return product


def get_product_by_modifier_item(venue_id, id_modifier):
    menu = list_menu(venue_id)
    for product in menu:
        for mod in product['modifiers']:
            for m_item in mod['items']:
                if m_item['id'] == id_modifier:
                    return product


def get_group_modifier_item(venue_id, product_code=None, product_id=None, order_mod_code=None, order_mod_id=None):
    product = get_product_from_menu(venue_id, product_code=product_code, product_id=product_id)
    if not product:
        modifiers = []
        for item in list_menu(venue_id):
            modifiers.extend(item.get('modifiers'))
    else:
        modifiers = product.get('modifiers', [])
    for mod in modifiers:
        for m_item in mod.get('items', []):
            if m_item.get('code') == order_mod_code or m_item.get('id') == order_mod_id:
                return m_item


def get_group_modifier(venue_id, group_id, modifier_id):
    menu = get_menu(venue_id, filtered=False)
    group_modifiers, modifiers = _get_menu_modifiers(menu)
    items = group_modifiers[group_id]['items']
    for item in items:
        if item['id'] == modifier_id:
            return item


def get_promo_by_id(venue_id, promo_id):
    promos = get_venue_promos(venue_id)
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
            product = get_group_modifier_item(order.venue_id, order_mod_id=item['id'])
        if not product:
            logging.error('product is not found in menu!')
            continue
        item['code'] = product['code']
        item['sum'] = product['price'] * item['amount'] - item.get('discount_sum', 0)
        if item['sum'] == 0:
            if 'modifiers' in item:
                for m in item['modifiers']:
                    mod_item = get_group_modifier_item(order.venue_id, product_code=item['code'], order_mod_id=m.get('id'))
                    m['code'] = mod_item.get('code')
                    m['sum'] = mod_item.get('price', 0) * m.get('amount', 0)
                item['sum'] = m['sum'] if item.get('modifiers') else 0
                item['code'] = m['code'] if item.get('modifiers') else item['code']


    url = '/orders/calculate_loyalty_discounts'
    payload = order_request
    company_id = Venue.venue_by_id(order.venue_id).company_id
    result = json.loads(__post_request(company_id, url, {}, payload))

    if result.get('availableFreeProducts'):
        for free_product in result.get('availableFreeProducts'):
            product = get_product_from_menu(order.venue_id, product_code=free_product.get('productCode'))
            if not product:
                modifier = get_group_modifier_item(order.venue_id, order_mod_code=free_product.get('productCode'))
                if modifier:
                    product = get_product_by_modifier_item(order.venue_id, modifier['id'])
                    logging.info(product)
                    free_product['modifiers'] = [{
                        'amount': 1,
                        'price': modifier['price'],
                        'id': modifier['id'],
                        'groupId': modifier['groupId'],
                        'name': modifier['name']
                    }]
            if product:
                free_product['id'] = product['productId']
                free_product['name'] = product['name']
                free_product['price'] = product['price'] if product['price'] else free_product['modifiers'][0]['price']
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
                        if not product:
                            product = get_group_modifier_item(order.venue_id, order_mod_code=detail.get('productCode'))
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


def get_delivery_terminals(venue_id):
    memcache_key = "deliveryTerminals_%s" % venue_id
    result = memcache.get(memcache_key)
    if not result:
        org_id = Venue.venue_by_id(venue_id).company_id
        response = __get_request(org_id, '/deliverySettings/getDeliveryTerminals', {
            'organization': venue_id
        })
        result = json.loads(response)['deliveryTerminals']
        memcache.set(memcache_key, result, time=24*3600)
    return result


def get_delivery_terminal_id(venue_id):
    terminals = get_delivery_terminals(venue_id)
    if terminals:
        return terminals[0]['deliveryTerminalId']
    return None


def get_customer_by_phone(company_id, phone, venue_id):
    result = __get_request(company_id, '/customers/get_customer_by_phone', {
        'organization': venue_id,
        'phone': phone
    })
    if result:
        return json.loads(result)
    else:
        return 'failure'


def get_customer_by_id(company_id, customer_id, venue_id):
    result = __get_request(company_id, '/customers/get_customer_by_id', {
        'organization': venue_id,
        'id': customer_id
    })
    return json.loads(result)


def create_or_update_customer(company_id, venue_id, data):
    result = __post_request(company_id, '/customers/create_or_update', {
        'organization': venue_id
    }, {'customer': data})
    return result.strip('"')


def get_orders(venue, start, end, status=None):
    start += timedelta(seconds=venue.get_timezone_offset())
    end += timedelta(seconds=venue.get_timezone_offset())
    payload = {
        'organization': venue.venue_id,
        'dateFrom': start.strftime("%Y-%m-%d %H:%M:%S"),
        'dateTo': end.strftime("%Y-%m-%d %H:%M:%S"),
        'requestTimeout': 20
    }
    if status:
        payload['deliveryStatus'] = status
    return json.loads(__get_request(venue.company_id, '/orders/deliveryOrders', payload))


def parse_iiko_time(time_str, venue):
    return datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S") - timedelta(seconds=venue.get_timezone_offset())

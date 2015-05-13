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

from models.iiko import CompanyNew, IikoApiLogin
from methods.image_cache import convert_url


OLD_IIKO_BASE_URL = 'https://iiko.net:9900/api/0'
NEW_IIKO_BASE_URL = 'https://iiko.biz:9900/api/0'

CAT_GIFTS_GROUP_ID = 'fca63e6b-b622-4d99-9453-b8c3372c6179'


def __get_iiko_base_url(company):
    return NEW_IIKO_BASE_URL if company.new_endpoints else OLD_IIKO_BASE_URL


def __get_request(company, api_path, params):
    def do():
        url = '%s%s' % (iiko_base_url, api_path)
        if params:
            url = '%s?%s' % (url, urllib.urlencode(params))
        logging.info(url)
        return urlfetch.fetch(url, deadline=30, validate_certificate=False)

    iiko_base_url = __get_iiko_base_url(company)
    params['access_token'] = get_access_token(company)
    result = do()
    if result.status_code == 401:
        logging.warning("bad token")
        params['access_token'] = get_access_token(company, refresh=True)
        result = do()
    return result.content


def __post_request(company, api_path, params, payload):
    def do():
        url = '%s%s' % (iiko_base_url, api_path)
        if params:
            url = '%s?%s' % (url, urllib.urlencode(params))
        json_payload = json.dumps(payload)
        logging.info("PAYLOAD %s" % str(json_payload))
        logging.info(url)

        return urlfetch.fetch(url, method='POST', headers={'Content-Type': 'application/json'}, payload=json_payload,
                              deadline=30, validate_certificate=False)

    iiko_base_url = __get_iiko_base_url(company)
    params['access_token'] = get_access_token(company)
    result = do()
    if result.status_code == 401:
        logging.warning("bad token")
        params['access_token'] = get_access_token(company, refresh=True)
        result = do()
    return result.content


def get_access_token(company, refresh=False):
    token = memcache.get('iiko_token_%s' % company.iiko_login)
    if not token or refresh:
        token = _fetch_access_token(company)
        memcache.set('iiko_token_%s' % company.iiko_login, token, time=10*60)
    return token


def _fetch_access_token(company):
    iiko_api_login = IikoApiLogin.get_by_id(company.iiko_login)
    data = urllib.urlencode({
        "user_id": iiko_api_login.login,
        "user_secret": iiko_api_login.password
    })
    result = urlfetch.fetch(
        __get_iiko_base_url(company) + '/auth/access_token?%s' % data, deadline=10, validate_certificate=False)
    return result.content.strip('"')


def get_stop_list(org_id):
    company = CompanyNew.get_by_iiko_id(org_id)
    result = __get_request(company, '/stopLists/getDeliveryStopList', {
        'organization': org_id,
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


def _fix_categories_images(menu):
    cat_stack = menu[:]
    i = 0
    while i < len(cat_stack):
        cat_stack.extend(cat_stack[i].get('children', []))
        i += 1
    for cat in cat_stack[::-1]:
        if cat['image']:
            continue
        if cat.get('children'):
            for child in cat['children']:
                if child['image']:
                    cat['image'].append(child['image'][0])
                    break
        else:
            for product in cat['products']:
                if product['images']:
                    cat['image'].append({'imageUrl': product['images'][0]})
                    break


def _clone(d):
    return json.loads(json.dumps(d))


def _load_menu(company):
    result = __get_request(company, '/nomenclature/%s' % company.iiko_org_id, {})
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

        if company.iiko_org_id == CompanyNew.VENEZIA:
            product['name'] = product['name'].lstrip("0123456789. ")
        if company.iiko_org_id == CompanyNew.COFFEE_CITY:
            product['weight'] = 0

        if company.iiko_org_id == CompanyNew.COFFEE_CITY and product['parentGroup'] == CAT_GIFTS_GROUP_ID:
            product['price'] = 1
            product['name'] += ' '

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
        if company.iiko_org_id == CompanyNew.SUSHILAR and cat['id'] == '6e4b8c9c-df45-40f6-8356-ac8039e3f630':
            continue
        if not cat['isIncludedInMenu']:
            continue
        if company.iiko_org_id == CompanyNew.COFFEE_CITY and cat['id'] == CAT_GIFTS_GROUP_ID:
            cat['parentGroup'] = None
            cat['order'] = 4
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

    menu = sorted(categories.values(), key=operator.itemgetter('order'))
    _fix_categories_images(menu)
    return menu


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


def get_menu(org_id, force_reload=False, filtered=True):
    menu = memcache.get('iiko_menu_%s' % org_id)
    if not menu or force_reload:
        company = CompanyNew.get_by_iiko_id(org_id)
        if not company.menu or force_reload:
            company.menu = _load_menu(company)
            company.put()
        menu = company.menu
        memcache.set('iiko_menu_%s' % org_id, menu, time=1*3600)
    if filtered:
        _filter_menu(menu)
    return menu


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


def prepare_order(order, customer, payment_type):
    company = CompanyNew.get_by_iiko_id(order.venue_id)
    local_date = order.date + timedelta(seconds=company.get_timezone_offset())
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
        obj['deliveryTerminalId'] = order.delivery_terminal_id
    else:
        order.delivery_terminal_id = None
        if order.venue_id == CompanyNew.ORANGE_EXPRESS:
            dt_mapping = {
                u"Одинцово": "2b20fde1-727f-e430-013e-203bb2e09905",
                u"Егорьевск": "7658baf0-cc65-28b5-014b-7cde6614cfbe",
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
        typ = company.get_payment_type(payment_type)
        obj['order']['paymentItems'][0]['paymentType']['code'] = typ.iiko_uuid
        if typ.type_id == 2:
            obj['order']['paymentItems'][0].update({
                'isProcessedExternally': True,
                'isExternal': True,
                'isPreliminary': True
            })

    return obj


def pre_check_order(company, order_dict):
    pre_check = __post_request(company, '/orders/checkCreate', {
        'requestTimeout': 30
    }, order_dict)
    logging.info(pre_check)
    return json.loads(pre_check)


def place_order(company, order_dict):
    result = __post_request(company, '/orders/add', {
        'requestTimeout': 30
    }, order_dict)
    logging.info(result)
    return json.loads(result)


def order_info(order):
    company = CompanyNew.get_by_iiko_id(order.venue_id)
    result = __get_request(company, '/orders/info', {
        'requestTimeout': 30,
        'organization': order.venue_id,
        'order': order.order_id
    })
    return json.loads(result)


def order_info1(order_id, org_id):
    company = CompanyNew.get_by_iiko_id(org_id)
    result = __get_request(company, '/orders/info', {
        'requestTimeout': 30,
        'organization': org_id,
        'order': order_id
    })
    logging.info(result)
    return json.loads(result)


def get_history(client_id, org_id):
    company = CompanyNew.get_by_iiko_id(org_id)
    result = __get_request(company, '/orders/deliveryHistory', {
        'organization': org_id,
        'customer': client_id,
        'requestTimeout': 20
    })
    obj = json.loads(result)
    return obj


def get_history_by_phone(phone, org_id):
    company = CompanyNew.get_by_iiko_id(org_id)
    result = __get_request(company, '/orders/deliveryHistoryByPhone', {
        'organization': org_id,
        'phone': phone
    })
    obj = json.loads(result)
    return obj


def get_payment_types(org_id):
    company = CompanyNew.get_by_iiko_id(org_id)
    result = __get_request(company, '/paymentTypes/getPaymentTypes', {
        'organization': org_id
    })
    obj = json.loads(result)
    return obj


def get_venue_promos(org_id):
    if org_id == CompanyNew.MIVAKO:
        from api.specials.mivako_promo import get_mivako_iiko_promos
        return get_mivako_iiko_promos()

    url = '/organization/%s/marketing_campaigns' % org_id
    company = CompanyNew.get_by_iiko_id(org_id)
    promos = json.loads(__get_request(company, url, {}))
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


def list_menu(org_id):

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

    menu = get_menu(org_id, filtered=False)
    queue = deque(menu)
    products = []
    while len(queue):
        cat = queue.popleft()
        if not cat['hasChildren']:
            products.extend(get_products(cat))
        else:
            queue.extend(get_categories(cat))

    return products


def get_product_from_menu(org_id, product_code=None, product_id=None):
    menu = list_menu(org_id)
    for product in menu:
        if product['productId'] == product_id or product['code'] == product_code:
            return product


def get_product_by_modifier_item(org_id, id_modifier):
    menu = list_menu(org_id)
    for product in menu:
        for mod in product['modifiers']:
            for m_item in mod['items']:
                if m_item['id'] == id_modifier:
                    return product


def get_group_modifier_item(org_id, product_code=None, product_id=None, order_mod_code=None, order_mod_id=None):
    product = get_product_from_menu(org_id, product_code=product_code, product_id=product_id)
    if not product:
        modifiers = []
        for item in list_menu(org_id):
            modifiers.extend(item.get('modifiers'))
    else:
        modifiers = product.get('modifiers', [])
    for mod in modifiers:
        for m_item in mod.get('items', []):
            if m_item.get('code') == order_mod_code or m_item.get('id') == order_mod_id:
                return m_item


def get_group_modifier(org_id, group_id, modifier_id):
    menu = get_menu(org_id, filtered=False)
    group_modifiers, modifiers = _get_menu_modifiers(menu)
    items = group_modifiers[group_id]['items']
    for item in items:
        if item['id'] == modifier_id:
            return item


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
    company = CompanyNew.get_by_iiko_id(order.venue_id)
    result = json.loads(__post_request(company, url, {}, payload))

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


def get_customer_by_phone(company, phone):
    result = __get_request(company, '/customers/get_customer_by_phone', {
        'organization': company.iiko_org_id,
        'phone': phone
    })
    return json.loads(result)


def get_customer_by_id(company, customer_id):
    result = __get_request(company, '/customers/get_customer_by_id', {
        'organization': company.iiko_org_id,
        'id': customer_id
    })
    return json.loads(result)


def create_or_update_customer(company, data):
    result = __post_request(company, '/customers/create_or_update', {
        'organization': company.iiko_org_id
    }, {'customer': data})
    return result.strip('"')


def get_orders(company, start, end, status=None):
    start += timedelta(seconds=company.get_timezone_offset())
    end += timedelta(seconds=company.get_timezone_offset())
    payload = {
        'organization': company.iiko_org_id,
        'dateFrom': start.strftime("%Y-%m-%d %H:%M:%S"),
        'dateTo': end.strftime("%Y-%m-%d %H:%M:%S"),
        'requestTimeout': 20
    }
    if status:
        payload['deliveryStatus'] = status
    return json.loads(__get_request(company, '/orders/deliveryOrders', payload))


def parse_iiko_time(time_str, company):
    return datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S") - timedelta(seconds=company.get_timezone_offset())


def get_orgs(iiko_api_login):
    dummy = CompanyNew(iiko_login=iiko_api_login)
    result = __get_request(dummy, '/organization/list', {})
    return json.loads(result)


def get_org(iiko_api_login, org_id):
    dummy = CompanyNew(iiko_login=iiko_api_login)
    result = __get_request(dummy, '/organization/%s' % org_id, {})
    return json.loads(result)

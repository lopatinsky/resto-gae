from collections import defaultdict
import json
import operator
from google.appengine.api import memcache
import webapp2
from methods.iiko.base import get_request, CAT_GIFTS_GROUP_ID
from methods.image_cache import convert_url
from models.iiko import CompanyNew
from collections import deque

__author__ = 'dvpermyakov'


def get_stop_list(org_id):
    company = CompanyNew.get_by_iiko_id(org_id)
    result = get_request(company, '/stopLists/getDeliveryStopList', {
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
    result = get_request(company, '/nomenclature/%s' % company.iiko_org_id, {})
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
            if company.iiko_org_id == CompanyNew.TYKANO and modifier['code'] in ('11111', '99999'):
                continue  # skip 'delivery' and 'takeout' modifiers for Tukano
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


def get_modifier_item(org_id, product_code=None, product_id=None, order_mod_code=None, order_mod_id=None):
    product = get_product_from_menu(org_id, product_code=product_code, product_id=product_id)
    for mod in product.get('modifiers', []):
        for m_item in mod.get('items', []):
            if m_item.get('code') == order_mod_code or m_item.get('id') == order_mod_id:
                return m_item
    for mod in product.get('single_modifiers', []):
        if mod.get('code') == order_mod_code or mod.get('id') == order_mod_id:
            return mod
    return None


def get_group_modifier(org_id, group_id, modifier_id):
    menu = get_menu(org_id, filtered=False)
    group_modifiers, modifiers = _get_menu_modifiers(menu)
    items = group_modifiers[group_id]['items']
    for item in items:
        if item['id'] == modifier_id:
            return item


def fix_modifier_amount(items):
    for item in items:
        if "modifiers" in item:
            for mod in item["modifiers"]:
                if mod["amount"] == 0 and mod.get("groupId"):
                    mod["amount"] = 1
            item["modifiers"] = [mod for mod in item["modifiers"] if mod["amount"]]
    return items

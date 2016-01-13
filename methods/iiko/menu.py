# coding=utf-8
import logging
from collections import defaultdict
import json
import operator
import webapp2
from methods.iiko.base import get_request, CAT_GIFTS_GROUP_ID
from methods.image_cache import convert_url
from methods.specials.cat import fix_cat_items
from models.iiko import CompanyNew
from collections import deque

from models.square_table import PickleStorage

__author__ = 'dvpermyakov'


def _load_stop_list(company):
    result = get_request(company, '/stopLists/getDeliveryStopList', {
        'organization': company.iiko_org_id,
    })
    stop_lists = json.loads(result)['stopList']
    result = {}
    for dt_stop_list in stop_lists:
        dt_dict = {}
        for item_info in dt_stop_list['items']:
            dt_dict[item_info['productId']] = item_info['balance']
        result[dt_stop_list['deliveryTerminalId']] = dt_dict
    return result


def get_company_stop_lists(company, force_reload=False):
    stop_lists = PickleStorage.get("stop_lists_%s" % company.iiko_org_id) if not force_reload else None
    if not stop_lists:
        stop_lists = _load_stop_list(company)
        PickleStorage.save("stop_lists_%s" % company.iiko_org_id, stop_lists)
    return stop_lists


def get_stop_list(company, delivery_terminal):
    return get_company_stop_lists(company).get(delivery_terminal.key.id(), {})


def _get_menu_modifiers(company, menu):
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
            group_name = g['name']
            if company.iiko_org_id == CompanyNew.HLEB:
                # name has format BLABLA_name_BLABLA
                name_split = group_name.split("_")
                if len(name_split) >= 2:
                    group_name = name_split[1]
            group_modifiers[g['id']].update({
                'groupId': g['id'],
                'name': group_name,
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
    group_modifiers, modifiers = _get_menu_modifiers(company, iiko_menu)
    category_products = defaultdict(list)

    if 'productCategories' in iiko_menu:
        iiko_categories = {c['id']: c['name'] for c in iiko_menu['productCategories']}
    else:
        iiko_categories = {}

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

        name = product['name']
        description = product['description']
        if company.iiko_org_id == CompanyNew.HLEB:
            if product['tags']:
                name = product['tags'][0]
            description = product['additionalInfo']

        category_products[product['parentGroup']].append({
            'price': product['price'],
            'name': name,
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
            'description': description or '',
            'additionalInfo': add_info,
            'additionalInfo1': add_info_str,
            'iikoCatId': product['productCategoryId'],
            'iikoCatName': iiko_categories.get(product['productCategoryId'], ''),
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
    if company.iiko_org_id == CompanyNew.MIVAKO:
        if "b918a490-e0f2-485c-bb13-3903cc5cc28d" in categories:
            menu = categories["b918a490-e0f2-485c-bb13-3903cc5cc28d"]['children']

    _fix_categories_images(menu)
    return menu


def _filter_menu(menu):
    def process_category(category):
        for p in category['products']:
            p['single_modifiers'] = [m
                                     for m in p['single_modifiers']
                                     if m['minAmount'] == 0]
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
    menu = PickleStorage.get("iiko_menu_%s" % org_id) if not force_reload else None
    if not menu:
        company = CompanyNew.get_by_iiko_id(org_id)
        menu = _load_menu(company)
        PickleStorage.save("iiko_menu_%s" % org_id, menu)
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
            product['extCatName'] = cat_dict['name']
            product['extCatId'] = cat_dict['id']
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


def _fix_modifier_amount(org_id, items):
    menu = list_menu(org_id)
    modifiers = {item['productId']: item['single_modifiers'] for item in menu}

    for item in items:
            item.setdefault("modifiers", [])
            # 1: fix zero amount for group modifiers
            for mod in item["modifiers"]:
                if mod["amount"] == 0 and mod.get("groupId"):
                    mod["amount"] = 1
            # 2: remove modifiers with zero amount
            item["modifiers"] = [mod for mod in item["modifiers"] if mod["amount"]]
            # 3: add required single modifiers
            item_modifiers = modifiers[item["id"]]
            for mod in item_modifiers:
                if mod["minAmount"] > 0:
                    item["modifiers"].append({
                        "id": mod["id"],
                        "amount": mod["minAmount"]
                    })


def _fill_item_info(org_id, items):
    for item in items:
        product = get_product_from_menu(org_id, product_id=item['id'])
        if not product:
            logging.error('product is not found in menu!')
            continue
        item['name'] = product['name']
        item['code'] = product['code']
        item['sum'] = product['price'] * item['amount']
        item['category'] = product['iikoCatName']
        item['ext_category_id'] = product['extCatId']

        for m in item.get('modifiers', []):
            mod_item = get_modifier_item(org_id, product_code=item['code'], order_mod_id=m.get('id'))
            m['name'] = mod_item.get('name')
            m['code'] = mod_item.get('code')
            m['sum'] = mod_item.get('price', 0) * m.get('amount', 0) * item['amount']
            item['sum'] += m['sum']


def prepare_items(company, items):
    if company.iiko_org_id == CompanyNew.EMPATIKA:
        items.append({
            'id': 'eaec4cb8-77d8-49c3-8de9-cfed938abe69',
            'amount': 1.0
        })
    elif company.iiko_org_id == CompanyNew.HLEB:
        items.append({
            'id': '5b3deff4-08ae-4ce4-b4ce-24f156aab324',
            'amount': 1.0
        })
    _fix_modifier_amount(company.iiko_org_id, items)
    _fill_item_info(company.iiko_org_id, items)
    if company.iiko_org_id == CompanyNew.COFFEE_CITY:
        fix_cat_items(items)
    return items


def add_additional_categories(company, menu):
    min_order = menu[0]['order']
    starting_order = min_order - len(company.additional_categories)
    additional_dicts = []
    for i, c in enumerate(company.additional_categories):
        products = [get_product_from_menu(company.iiko_org_id, product_id=item_id) for item_id in c.item_ids]
        products = filter(None, products)
        if products:
            additional_dicts.append({
                "name": c.title,
                "id": "additional$%s" % i,
                "parent": None,
                "hasChildren": False,
                "children": [],
                "image": [],
                "order": starting_order + i,
                "products": products
            })
    _fix_categories_images(additional_dicts)
    menu[0:0] = additional_dicts

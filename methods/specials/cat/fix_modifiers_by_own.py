# -*- coding: utf-8 -*-
from models.iiko import CompanyNew

__author__ = 'dvpermyakov'

BY_OWN_GROUP_MODIFIER_ID = '2d97e2a9-a35a-4712-8dd6-6df61b6b3831'
BY_OWN_MODIFIER_ID = '527f4d6e-0550-475c-98d8-7290111b60fe'
BY_OWN_GROUP_MODIFIER_NAME = u'С собой'

import logging


def remove_modifiers(menu):
    for item in menu:
        for product in item['products']:
            if product['modifiers']:
                for modifier in product['modifiers'][:]:
                    if modifier['groupId'] == BY_OWN_GROUP_MODIFIER_ID:
                        product['modifiers'].remove(modifier)
                        break
    return menu


def set_modifier_by_own(items):
    from methods.iiko.menu import get_product_from_menu

    for item in items:
        product = get_product_from_menu(CompanyNew.COFFEE_CITY, product_id=item['id'])
        logging.info(product)
        if product.get('modifiers'):
            for modifier in product['modifiers']:
                if modifier['groupId'] == BY_OWN_GROUP_MODIFIER_ID:
                    new_modifier = {
                        'groupId': modifier['groupId'],
                        'groupName': modifier['name'],
                        'name': BY_OWN_GROUP_MODIFIER_NAME,
                        'id': BY_OWN_MODIFIER_ID,
                        'amount': 1
                    }
                    if item.get('modifiers'):
                        item['modifiers'].append(new_modifier)
                    else:
                        item['modifiers'] = [new_modifier]
    return items


def remove_modifiers_from_item(item):
    for m in item['modifiers'][:]:
        if m['groupId'] == BY_OWN_GROUP_MODIFIER_ID:
            item['modifiers'].remove(m)

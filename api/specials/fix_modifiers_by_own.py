# -*- coding: utf-8 -*-
__author__ = 'dvpermyakov'

BY_OWN_GROUP_MODIFIER_ID = '2d97e2a9-a35a-4712-8dd6-6df61b6b3831'
BY_OWN_MODIFIER_ID = '527f4d6e-0550-475c-98d8-7290111b60fe'
BY_OWN_GROUP_MODIFIER_NAME = u'С собой'

from methods import iiko_api
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


def set_modifier_by_own(iiko_org_id, items):
    for item in items:
        product = iiko_api.get_product_from_menu(iiko_org_id, product_id=item['id'])
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

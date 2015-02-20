# -*- coding: utf-8 -*-
__author__ = 'dvpermyakov'

import logging

SYROPS_ID = '9b9c2b5e-8b0a-48e5-8703-8cb8d0e6b1ec'
DRINKS_ID = '494df59c-34d3-4e6d-98e8-8c6e020a2f6a'
WITHOUT_SYROP_ID = '123456789012345678901234567890'


def set_syrop_modifiers(menu):
    syrops = None
    drinks = None
    for item in menu:
        if item['id'] == SYROPS_ID:
            syrops = item
        elif item['id'] == DRINKS_ID:
            drinks = item

    if not syrops or not drinks:
        return menu

    for drink in drinks['products']:
        syrop_modifier = {
            "maxAmount": 1,
            "minAmount": 1,
            "name": syrops['name'],
            "groupId": syrops['id'],
            "items": [{
                "groupId": syrops['id'],
                "price": 0,
                "amount": 1,
                "name": "Без Сиропа",
                "id": WITHOUT_SYROP_ID
            }]
        }
        for syrop in syrops['products']:
            syrop_modifier['items'].append({
                "groupId": syrops['id'],
                "price": syrop['price'],
                "amount": 1,
                "name": syrop['name'],
                "id": syrop['productId']
            })
        drink['modifiers'].append(syrop_modifier)

    menu.remove(syrops)
    logging.info(menu)
    return menu


def set_syrop_items(items):
    for item in items[:]:
        modifiers = item.get('modifiers')
        if modifiers:
            for modifier in modifiers[:]:
                if modifier['groupId'] == SYROPS_ID:
                    if modifier['id'] != WITHOUT_SYROP_ID:
                        items.append({
                            'name': modifier['name'],
                            'id': modifier['id'],
                            'amount': modifier['amount']
                        })
                    modifiers.remove(modifier)
    return items
# coding=utf-8

__author__ = 'Ex0rc1st'

SUSHI_TIME_MODIFIER_ID = '802b59e5-b639-4f32-a12c-a986e1ab9e66'


def remove_modifier_from_menu(menu):
    def process_category(cat):
        for subcat in cat['children']:
            process_category(subcat)
        for item in cat['products']:
            item['single_modifiers'] = [m
                                        for m in item['single_modifiers']
                                        if m['id'] != SUSHI_TIME_MODIFIER_ID]
    for root_category in menu:
        process_category(root_category)


def add_modifier_to_items(items):
    from methods.iiko.menu import list_menu
    from models.iiko.company import CompanyNew

    menu = list_menu(CompanyNew.SUSHI_TIME)
    ids_with_modifier = set()
    for item in menu:
        print item['productId'], list((m['id'] for m in item['single_modifiers']))
        if SUSHI_TIME_MODIFIER_ID in (m['id'] for m in item['single_modifiers']):
            ids_with_modifier.add(item['productId'])
    print ids_with_modifier
    for item in items:
        if item['id'] in ids_with_modifier:
            item.setdefault("modifiers", []).append({
                "id": SUSHI_TIME_MODIFIER_ID,
                "name": "",
                "amount": 1,
            })

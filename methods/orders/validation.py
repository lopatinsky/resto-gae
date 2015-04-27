# coding=utf-8
from methods import iiko_api

__author__ = 'dvpermyakov'


def check_stop_list(items, delivery):
    for item in items:
        item_id = item.get('id')
        item = iiko_api.get_product_from_menu(delivery.iiko_organization_id, product_id=item_id)
        if not item:
            return True, None
        if item_id in delivery.item_stop_list:
            return False, u'Продукт %s был помещен в стоп-лист' % item.get('name')
        else:
            return True, None
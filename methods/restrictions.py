#coding=utf-8
__author__ = 'dvpermyakov'

from collections import deque
from methods.iiko_api import get_menu
from working_hours import is_datetime_valid
from datetime import datetime


def restrict_product_by_time(order_dict, restriction_array):

    def get_products_by_category(menu, category_id):

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

        queue = deque(menu)
        products = []
        while len(queue):
            cat = queue.popleft()
            if cat['id'] == category_id:
                queue.clear()
                products = []
            if not cat['hasChildren']:
                products.extend(get_products(cat))
            else:
                queue.extend(get_categories(cat))
        return products

    item_ids = []
    for item in order_dict['order']['items']:
        if item['id'] not in item_ids:
            item_ids.append(item['id'])

    menu = get_menu(venue_id=order_dict['restaurantId'])
    for restriction in restriction_array:
        restricted_products = get_products_by_category(menu, restriction['category_id'])
        restricted_product_ids = [product['productId'] for product in restricted_products]
        schedule = restriction['schedule']
        for item_id in item_ids:
            if item_id in restricted_product_ids and\
                    not is_datetime_valid(schedule, datetime.strptime(order_dict['order']['date'], '%Y-%m-%d %H:%M:%S')):
                return u'Продукт id=%s запрещен' % item_id
# coding=utf-8

_TEN_PERCENT_ALWAYS_CATEGORY = "b934ff20-8f86-46d2-b438-090b8fc3c0cf"


def apply_lpq_discounts(order):
    for item in order.items:
        print item['category_id']
        if item['category_id'] == _TEN_PERCENT_ALWAYS_CATEGORY:
            discount = 0.1 * item['sum']
            item['discount_sum'] = discount
            item['sum'] -= discount
            order.discount_sum += discount

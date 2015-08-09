import logging
from methods.iiko.promo import get_order_promos, set_discounts, add_bonus_to_payment, set_gifts

__author__ = 'dvpermyakov'


def set_discounts_bonuses_gifts(order, order_dict, discount_sum, bonus_sum, gifts):
    logging.info('discount %s' % discount_sum)
    logging.info('bonus %s' % bonus_sum)
    logging.info('gifts %s' % gifts)

    promos = get_order_promos(order, order_dict)
    if discount_sum != 0:
        set_discounts(order, order_dict['order'], promos)
        if order.discount_sum != discount_sum:
            logging.info('conflict_discount: app(%s), iiko(%s)' % (discount_sum, order.discount_sum))
            return False
        promos = get_order_promos(order, order_dict)
    if bonus_sum != 0:
        if bonus_sum != promos['maxPaymentSum']:
            logging.info('conflict_max_bonus: app(%s), iiko(%s)' % (bonus_sum, promos['maxPaymentSum']))
            return False
        add_bonus_to_payment(order_dict['order'], bonus_sum, True)
        order.bonus_sum = bonus_sum

    if gifts:
        if not promos.get('availableFreeProducts'):
            logging.info('conflict_gift: app(%s), iiko(%s)' % (gifts, None))
            return False

        def get_iiko_item(items, cur_item):
            for item in items:
                if item['id'] == cur_item['id']:
                    return item
            return None

        iiko_gifts = []
        for gift in gifts:
            iiko_gift = get_iiko_item(promos.get('availableFreeProducts'), gift)
            if not iiko_gift:
                logging.info('conflict_gift: app(%s), iiko(%s)' % (gift, None))
                return False
            else:
                iiko_gift['amount'] = gift.get('amount', 1)
                iiko_gifts.append(iiko_gift)
        set_gifts(order, order_dict['order'], iiko_gifts)

    return True

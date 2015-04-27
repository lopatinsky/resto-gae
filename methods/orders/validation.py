# coding=utf-8
from datetime import timedelta
import logging
from config import config
from methods import iiko_api, working_hours

__author__ = 'dvpermyakov'


def check_stop_list(items, delivery):
    for item in items:
        item_id = item.get('id')
        item = iiko_api.get_product_from_menu(delivery.iiko_organization_id, product_id=item_id)
        if not item:
            logging.warning("Item is not found")
        if item_id in delivery.item_stop_list:
            return False, u'Продукт %s был помещен в стоп-лист' % item.get('name')
    return True, None


def check_company_schedule(company, order):
    local_time = order.date + timedelta(seconds=company.get_timezone_offset())
    if company.schedule:
        if not working_hours.is_datetime_valid(company.schedule, local_time):
            if config.CHECK_SCHEDULE:
                start, end = working_hours.parse_company_schedule(company.schedule, local_time.isoweekday())
                return False, u'Заказы будут доступны c %s до %s. Попробуйте в следующий раз.' % (start, end)
    return True, None


def check_config_restrictions(company, order_dict):
    for restriction in config.RESTRICTIONS:
        if company.iiko_org_id in restriction['venues']:
            error = restriction['method'](order_dict, restriction['venues'][company.iiko_org_id])
            if error:
                return False, error
    return True, None
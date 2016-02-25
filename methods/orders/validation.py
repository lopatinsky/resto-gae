# coding=utf-8
from collections import defaultdict
from datetime import timedelta, datetime
import logging
from math import floor

from methods import working_hours
from methods.iiko.menu import get_product_from_menu, get_stop_list
from models.iiko.company import CompanyNew

__author__ = 'dvpermyakov'


def _check_customer(customer):
    if not customer.phone:
        return False, u"Номер телефона имеет неверный формат. "
    return True, None


def _check_company_schedule(company, delivery_terminal, order):
    local_time = order.date + timedelta(seconds=company.get_timezone_offset())
    schedule = None
    holiday_schedule = None
    if company.schedule:
        schedule = company.schedule
        holiday_schedule = company.holiday_schedule
    if delivery_terminal and delivery_terminal.schedule:
        schedule = delivery_terminal.schedule
        holiday_schedule = delivery_terminal.holiday_schedule
    if schedule:
        if not working_hours.is_datetime_valid(schedule, local_time, order.is_delivery, holiday_schedule):
            start, end = working_hours.parse_company_schedule(schedule, local_time.date(), order.is_delivery,
                                                              holiday_schedule)
            order_type_str = u'доставки' if order.is_delivery else u'получения заказа'
            return False, u'Вы выбрали некорректное время %s. ' \
                          u'Пожалуйста, выберите время между %s:00 и %s:00.' % (order_type_str, start, end)
    return True, None


def _check_min_sum(company, order):
    if order.is_delivery and company.min_order_sum and order.sum < company.min_order_sum:
        return False, u"Минимальная сумма заказа %s рублей!" % company.min_order_sum
    return True, None


def _check_delivery_time(order):
    MAX_TIME_LOSS = 3 * 60
    logging.info(order.date)
    logging.info(datetime.utcnow())
    if not order.delivery_type:
        return False, u'Тип доставки не найден'
    if not order.delivery_type.available:
        return False, u'Тип доставки недоступен'
    if order.delivery_type.min_time:
        if order.date < datetime.utcnow() + timedelta(seconds=order.delivery_type.min_time-MAX_TIME_LOSS):
            return False, u'Пожалуйста, выберите время, большее текущего времени на %s минут.' % (order.delivery_type.min_time / 60)
    if order.date < datetime.utcnow() - timedelta(seconds=MAX_TIME_LOSS):
        return False, u"Пожалуйста, выберите время, большее текущего времени."
    return True, None


def _check_address(order):
    if order.address and not order.address.get("home", '').strip():
        return False, u"Не введен номер дома. Пожалуйста, введите его и попробуйте еще раз."
    return True, None


def _check_payment_type(company, order):
    payment_type = company.get_payment_type(order.payment_type)
    if payment_type and not payment_type.available:
        return False, u"Выбранный способ оплаты недоступен."
    return True, None


def _check_our_stop_list(delivery_terminal, order):
    if delivery_terminal:
        for item in order.items:
            item_id = item.get('id')
            item = get_product_from_menu(delivery_terminal.iiko_organization_id, product_id=item_id)
            if not item:
                logging.warning("Item is not found")
            if item_id in delivery_terminal.item_stop_list:
                return False, u'Продукт %s был помещен в стоп-лист' % item.get('name')
    return True, None


def _check_iiko_stop_list(company, delivery_terminal, order):
    stop_list = None
    if delivery_terminal:
        stop_list = get_stop_list(company, delivery_terminal)
    if not stop_list:
        return True, None

    quantity_dict = defaultdict(lambda: 0)
    for item in order.items:
        quantity_dict[item['id']] += item['amount']
        for modifier in item['modifiers']:
            quantity_dict[modifier['id']] += modifier['amount'] * item['amount']

    def _check(sl, item_id, name, amount, is_modifier):
        sl_amount = sl.get(item_id)
        if sl_amount is None:
            return True, None
        sl_amount = int(floor(sl_amount))
        if sl_amount <= 0:
            if is_modifier:
                return False, u'К сожалению, наименование "%s" отсутствует, ' \
                              u'выберите другое из списка' % name
            return False, u'Продукт "%s" закончился или недоступен в этом заведении' % name
        elif amount > sl_amount:
            return False, u'В этом заведении осталось только %sшт. "%s"' % (sl_amount, name)
        return True, None

    all_errors = []

    for item in order.items:
        success, error = _check(stop_list, item['id'], item['name'], quantity_dict[item['id']], False)
        if not success:
            item['errors'].append(error)
            all_errors.append(error)
        for modifier in item['modifiers']:
            success, error = _check(stop_list, modifier['id'], modifier['name'], quantity_dict[modifier['id']], True)
            if not success:
                item['errors'].append(error)
                all_errors.append(error)
    if all_errors:
        return False, all_errors[0]
    return True, None


def _check_stop_list(company, delivery_terminal, order):
    if company.iiko_stop_lists_enabled:
        return _check_iiko_stop_list(company, delivery_terminal, order)
    elif company.iiko_org_id == CompanyNew.COFFEE_CITY:
        return _check_our_stop_list(delivery_terminal, order)

    return True, None


def validate_order(company, delivery_terminal, order, customer):
    valid = True
    errors = []
    valid_condition, error = _check_company_schedule(company, delivery_terminal, order)
    if not valid_condition:
        valid = False
        errors.append(error)
    valid_condition, error = _check_customer(customer)
    if not valid_condition:
        valid = False
        errors.append(error)
    valid_condition, error = _check_min_sum(company, order)
    if not valid_condition:
        valid = False
        errors.append(error)
    valid_condition, error = _check_stop_list(company, delivery_terminal, order)
    if not valid_condition:
        valid = False
        errors.append(error)
    valid_condition, error = _check_payment_type(company, order)
    if not valid_condition:
        valid = False
        errors.append(error)
    valid_condition, error = _check_delivery_time(order)
    if not valid_condition:
        valid = False
        errors.append(error)
    valid_condition, error = _check_address(order)
    if not valid_condition:
        valid = False
        errors.append(error)
    return {
        'valid': valid,
        'errors': errors
    }

# coding=utf-8
from datetime import timedelta, datetime
import logging
from methods import working_hours
from methods.iiko.menu import get_product_from_menu

__author__ = 'dvpermyakov'


def _check_customer(customer):
    if not customer.phone:
        return False, u"Номер телефона имеет неверный формат. "
    return True, None


def _check_company_schedule(company, order):
    local_time = order.date + timedelta(seconds=company.get_timezone_offset())
    if company.schedule:
        if not working_hours.is_datetime_valid(company.schedule, local_time, order.is_delivery):
            start, end = working_hours.parse_company_schedule(company.schedule, local_time.isoweekday(),
                                                              order.is_delivery)
            return False, u'Вы выбрали некорректное время доставки. ' \
                          u'Пожалуйста, выберите время между %s:00 и %s:00.' % (start, end)
    return True, None


def _check_min_sum(company, order):
    if company.min_order_sum and order.sum < company.min_order_sum:
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


def _check_stop_list(delivery_terminal, order):
    if delivery_terminal:
        for item in order.items:
            item_id = item.get('id')
            item = get_product_from_menu(delivery_terminal.iiko_organization_id, product_id=item_id)
            if not item:
                logging.warning("Item is not found")
            if item_id in delivery_terminal.item_stop_list:
                return False, u'Продукт %s был помещен в стоп-лист' % item.get('name')
    return True, None


def validate_order(company, delivery_terminal, order, customer):
    valid = True
    errors = []
    valid_condition, error = _check_company_schedule(company, order)
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
    valid_condition, error = _check_stop_list(delivery_terminal, order)
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

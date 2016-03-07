import logging

from methods.auto.request import update_number_in_auto
from methods.iiko.order import order_info1
from methods.orders.approve import approve
from methods.rendering import parse_iiko_time
from models.iiko import CompanyNew, Order, Customer, OrderChangeLog, OrderChangeLogEntry
from methods.orders.close import close
from methods.orders.cancel import cancel
from models.iiko.order import IIKO_SOURCE, APP_SOURCE, AUTO_APP_SOURCE

__author__ = 'dvpermyakov'


def ___create_change_log(order, changes):
    if not changes:
        return None
    log = OrderChangeLog(order_id=order.order_id)
    log.changes = [OrderChangeLogEntry(what=name, old=old, new=getattr(order, name))
                   for name, old in changes.items()]
    log.put()
    return log


def __handle_changes(order, changes):
    ___create_change_log(order, changes)

    if 'number' in changes and order.source == AUTO_APP_SOURCE:
        update_number_in_auto(order)

    if 'status' in changes:
        if order.status == Order.CLOSED:
            close(order)
        elif order.status == Order.CANCELED:
            cancel(order)
        elif order.status == Order.APPROVED:
            approve(order)


def do_load(order, order_id, org_id, iiko_order=None):
    if not iiko_order:
        iiko_order = order_info1(order_id, org_id)
    company = CompanyNew.get_by_iiko_id(org_id)
    changes = {}

    no_new_value = object()

    def _attr(name, new_value=no_new_value):
        old_value = getattr(order, name)
        if new_value is no_new_value:
            new_value = iiko_order[name]
        if old_value != new_value:
            changes[name] = old_value
            setattr(order, name, new_value)

    if not order:
        changes['order'] = None
        order = Order(order_id=order_id, venue_id=org_id, source=IIKO_SOURCE)
        order.is_delivery = iiko_order['orderType']['orderServiceType'] == 'DELIVERY_BY_COURIER'
        customer = Customer.customer_by_customer_id(iiko_order['customerId'])
        order.customer = customer.key if customer else None  # TODO create customer

    new_sum = iiko_order['sum']
    for payment in iiko_order['payments']:
        if 'INET' in payment['paymentType']['code']:
            new_sum -= payment['sum']
    _attr('sum', new_sum)

    _attr('items')
    _attr('address')
    _attr('number')

    delivery_terminal_id = None
    if iiko_order['deliveryTerminal']:
        delivery_terminal_id = iiko_order['deliveryTerminal']['deliveryTerminalId']
    _attr('delivery_terminal_id', delivery_terminal_id)

    date = parse_iiko_time(iiko_order['deliveryDate'], company)
    _attr('date', date)

    created_time = parse_iiko_time(iiko_order['createdTime'], company)
    _attr('created_in_iiko', created_time)

    status = Order.parse_status(iiko_order['status'])
    if status == Order.CLOSED and iiko_order['sum'] < 0.005:
        status = Order.CANCELED
    _attr('status', status)

    logging.debug("changes in %s: %s", order_id, changes.keys())
    if changes and order.source in [APP_SOURCE, AUTO_APP_SOURCE]:
        __handle_changes(order, changes)
    order.put()
    return order

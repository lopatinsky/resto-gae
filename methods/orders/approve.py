from methods.auto.request import confirm_order
from methods.parse_com import send_order_status_push
from models.auto import AutoVenue
from models.iiko import DeliveryTerminal

__author__ = 'dvpermyakov'


def approve(order):
    delivery_terminal = DeliveryTerminal.get_by_id(order.delivery_terminal_id)
    auto_venue = AutoVenue.query(AutoVenue.delivery_terminal == delivery_terminal.key).get()
    if auto_venue:
        confirm_order(order, auto_venue)
    else:
        send_order_status_push(order)

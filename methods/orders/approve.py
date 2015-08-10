from methods.parse_com import send_order_status_push

__author__ = 'dvpermyakov'


def approve(order):
    send_order_status_push(order)

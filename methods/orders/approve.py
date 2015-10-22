# coding=utf-8
from methods.auto.request import confirm_order
from methods.parse_com import send_order_status_push
from models.iiko.company import CompanyNew
from models.iiko.order import AUTO_APP_SOURCE

__author__ = 'dvpermyakov'


def approve(order):
    company = CompanyNew.get_by_iiko_id(order.venue_id)
    if company.auto_token and order.source == AUTO_APP_SOURCE:
        confirm_order(order, company.auto_token)
    send_order_status_push(order)

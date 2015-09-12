# coding=utf-8
from models.iiko import DeliveryTerminal, PaymentType
from .base import BaseReportHandler
from datetime import datetime
from models import iiko

__author__ = 'dvpermyakov'


class OrdersReportHandler(BaseReportHandler):
    def get(self):
        org_id = self.request.get("selected_company")
        if org_id == '0':
            org_id = None
        start, end = self.get_date_range()

        terminals = {}
        for terminal in (DeliveryTerminal.query(DeliveryTerminal.iiko_organization_id == org_id).fetch()
                         if org_id else DeliveryTerminal.query().fetch()):
            terminals[terminal.key.id()] = terminal.name

        query = iiko.Order.query(iiko.Order.date > start, iiko.Order.date < end)
        if org_id:
            query = query.filter(iiko.Order.venue_id == org_id)
        orders = query.fetch()
        for order in orders:
            order.status_str = iiko.Order.STATUS_MAPPING[order.status][0]
            order.venue_name = iiko.CompanyNew.get_by_iiko_id(order.venue_id).app_title
            order.terminal_name = terminals.get(order.delivery_terminal_id, u'Не найдено')
            customer = order.customer.get() if order.customer else None
            order.customer_id = customer.customer_id if customer else '-'
            order.customer_name = customer.name if customer else '-'
            order.customer_phone = customer.phone if customer else '-'
            order.new_items = []
            for item in order.items:
                order.new_items.append({
                    'name': item['name'],
                    'amount': item['amount']
                })
            if order.payment_type == PaymentType.CASH:
                order.payment_name = 'CASH'
            elif order.payment_type == PaymentType.CARD:
                order.payment_name = 'CARD'
            else:
                order.payment_name = 'UNKNOWN'
        values = {
            'companies': iiko.CompanyNew.query().fetch(),
            'orders': orders,
            'chosen_company': iiko.CompanyNew.get_by_iiko_id(org_id),
            'start': start,
            'end': end
        }
        self.render_report('orders', values)

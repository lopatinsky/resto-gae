# coding=utf-8
from models.iiko import DeliveryTerminal

__author__ = 'dvpermyakov'

from ..base import BaseHandler
from datetime import datetime
from models import iiko
from report_methods import PROJECT_STARTING_YEAR, suitable_date


class OrdersReportHandler(BaseHandler):
    def get(self):
        org_id = self.request.get("selected_company")
        chosen_year = self.request.get_range("selected_year")
        chosen_month = self.request.get_range("selected_month")
        chosen_day = self.request.get_range("selected_day")
        if not chosen_year:
            chosen_month = 0
        if not chosen_month:
            chosen_day = 0
        if not org_id:
            chosen_year = datetime.now().year
            chosen_month = datetime.now().month
            chosen_day = datetime.now().day
        if org_id == '0':
            org_id = None

        terminals = {}
        for terminal in (DeliveryTerminal.query(DeliveryTerminal.iiko_organization_id == org_id).fetch()
                         if org_id else DeliveryTerminal.query().fetch()):
            terminals[terminal.key.id()] = terminal.name

        start = suitable_date(chosen_day, chosen_month, chosen_year, True)
        end = suitable_date(chosen_day, chosen_month, chosen_year, False)
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
            if order.payment_type == iiko.Order.CASH:
                order.payment_name = 'CASH'
            elif order.payment_type == iiko.Order.CARD:
                order.payment_name = 'CARD'
            else:
                order.payment_name = 'UNKNOWN'
        values = {
            'companies': iiko.CompanyNew.query().fetch(),
            'orders': orders,
            'chosen_company': iiko.CompanyNew.get_by_iiko_id(org_id),
            'start_year': PROJECT_STARTING_YEAR,
            'end_year': datetime.now().year,
            'chosen_year': chosen_year,
            'chosen_month': chosen_month,
            'chosen_day': chosen_day
        }
        self.render('reported_orders.html', **values)
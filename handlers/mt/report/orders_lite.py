# coding=utf-8
from models.iiko import DeliveryTerminal

__author__ = 'dvpermyakov'

from ..base import BaseHandler
from datetime import datetime
from models import iiko
from report_methods import PROJECT_STARTING_YEAR, suitable_date


class OrdersLiteReportHandler(BaseHandler):
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

        start = suitable_date(chosen_day, chosen_month, chosen_year, True)
        end = suitable_date(chosen_day, chosen_month, chosen_year, False)
        query = iiko.Order.query(iiko.Order.date > start, iiko.Order.date < end,
                                 iiko.Order.status == iiko.Order.CLOSED)
        if org_id:
            query = query.filter(iiko.Order.venue_id == org_id)
        orders = query.fetch()

        company_map = {}
        def get_company(iiko_org_id):
            if iiko_org_id not in company_map:
                company_map[iiko_org_id] = iiko.CompanyNew.get_by_iiko_id(order.venue_id)
            return company_map[iiko_org_id]

        dt_map = {}
        def get_dt(dt_id):
            if not dt_id:
                return None
            if dt_id not in dt_map:
                dt_map[dt_id] = DeliveryTerminal.get_by_id(dt_id)
            return dt_map[dt_id]

        for order in orders:
            order.status_str = iiko.Order.STATUS_MAPPING[order.status][0]
            order.venue_name = get_company(order.venue_id).app_title
            if order.payment_type == iiko.PaymentType.CASH:
                order.payment_name = 'CASH'
            elif order.payment_type == iiko.PaymentType.CARD:
                order.payment_name = 'CARD'
            elif order.payment_type == iiko.PaymentType.COURIER_CARD:
                order.payment_name = 'COURIER_CARD'
            else:
                order.payment_name = 'UNKNOWN'
            dt = get_dt(order.delivery_terminal_id)
            order.delivery_terminal_name = dt.name if dt else order.delivery_terminal_id
        values = {
            'companies': iiko.CompanyNew.query().fetch(),
            'orders': orders,
            'chosen_company': get_company(org_id) if org_id else None,
            'start_year': PROJECT_STARTING_YEAR,
            'end_year': datetime.now().year,
            'chosen_year': chosen_year,
            'chosen_month': chosen_month,
            'chosen_day': chosen_day
        }
        self.render('reported_orders_lite.html', **values)

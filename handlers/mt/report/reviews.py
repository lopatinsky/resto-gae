# coding=utf-8
from models.iiko import DeliveryTerminal
from models import iiko
from models.iiko.customer import IOS_DEVICE, ANDROID_DEVICE
from .base import BaseReportHandler

__author__ = 'dvpermyakov'


class ReviewsReportHandler(BaseReportHandler):
    def get(self):
        org_id = self.request.get("selected_company")
        if org_id == '0':
            org_id = None

        start, end = self.get_date_range()
        query = iiko.Order.query(iiko.Order.date > start, iiko.Order.date < end)
        if org_id:
            query = query.filter(iiko.Order.venue_id == org_id)
        orders = query.fetch()

        company_map = {}
        def get_company(iiko_org_id):
            if iiko_org_id not in company_map:
                company_map[iiko_org_id] = iiko.CompanyNew.get_by_iiko_id(iiko_org_id)
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

            customer = order.customer.get() if order.customer else None
            order.customer_id = customer.customer_id if customer else '-'
            order.customer_name = customer.name if customer else '-'
            order.customer_phone = customer.phone if customer else '-'

            order.customer_device = '-'
            if customer:
                device_type = customer.get_device()
                if device_type == IOS_DEVICE:
                    order.customer_device = 'iOS'
                elif device_type == ANDROID_DEVICE:
                    order.customer_device = 'Android'

            if not order.rate:
                order.hlcolor = ''
            elif 0 < order.rate.meal_rate < 3.5 or 0 < order.rate.service_rate < 3.5:
                order.hlcolor = '#ff8888'
            else:
                order.hlcolor = '#88ff88'
        values = {
            'companies': iiko.CompanyNew.query().fetch(),
            'orders': orders,
            'chosen_company': get_company(org_id) if org_id else None,
            'start': start,
            'end': end
        }
        self.render_report('reviews', values)

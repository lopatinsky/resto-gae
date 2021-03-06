# -*- coding: utf-8 -*-
import logging
from methods.iiko.history import get_orders
from methods.iiko.organization import get_payment_types
from .base import BaseReportHandler
from models import iiko
from datetime import datetime

__author__ = 'dvpermyakov'


class VenueReportHandler(BaseReportHandler):
    IIKO_STATUS_MAPPING = {
        iiko.Order.CLOSED: "CLOSED",
        iiko.Order.CANCELED: "CANCELLED",
        iiko.Order.NOT_APPROVED: "UNCONFIRMED"
    }

    VENUES_WITHOUT_IIKO_PAYMENT_TYPES = [
        iiko.CompanyNew.ORANGE_EXPRESS,  # Оранжеваый эксперсс
        iiko.CompanyNew.COFFEE_CITY,     # Coffee and the City
        iiko.CompanyNew.TYKANO           # Tykano
    ]

    def get_payment_types(self, source, company):
        if source == "app":
            result = []
            for payment in company.payment_types:
                payment = payment.get()
                result.append({
                    'type': payment.type_id,
                    'name': payment.name
                })
            return result

        elif source == "iiko":
            try:
                payments = get_payment_types(company.iiko_org_id)['paymentTypes']
            except Exception as e:
                text = str(e)
                logging.info('in payments in company %s' % company.app_title)
                logging.info(text)
                payments = []
            return [{
                'type': payment['code'],
                'name': payment['name']
            } for payment in payments]

    def get_app_companies_info(self, start, end, statuses):
        orders = iiko.Order.query(iiko.Order.date >= start, iiko.Order.date <= end).fetch()
        companies = iiko.CompanyNew.query().fetch()

        company_ids = {}
        for company in companies:
            payments = self.get_payment_types("app", company)
            company.payments = payments
            company.info = {}
            for payment in payments:
                payment = payment['type']
                company.info[payment] = {}
                for status in statuses:
                    info_dict = {
                        "orders_number": 0,
                        "orders_sum": 0,
                        "client_number": 0,
                        "goods_number": 0
                    }
                    company.info[payment][status] = info_dict
            company_ids[company.iiko_org_id] = company

        client_ids = []
        for order in orders:
            company = company_ids[order.venue_id]
            if order.status not in statuses:
                continue
            company.info[int(order.payment_type)][order.status]['orders_number'] += 1
            company.info[int(order.payment_type)][order.status]['orders_sum'] += order.sum
            company.info[int(order.payment_type)][order.status]['goods_number'] += len(order.items)
            if order.customer.id() not in client_ids:
                client_ids.append(order.customer.id())
                company.info[int(order.payment_type)][order.status]['client_number'] += 1

        return company_ids.values()

    def get_iiko_companies_info(self, start, end, statuses):
        companies = iiko.CompanyNew.query().fetch()

        for company in companies:
            confirmed = bool(self.request.get(str(company.key.id())))
            if not confirmed:
                continue
            try:
                orders = get_orders(company, start, end, status=None)
            except Exception as e:
                text = str(e)
                logging.info('in orders in company %s' % company.app_title)
                logging.info(text)
                orders = {}
                company.app_title += u' (IIKO DEADLINE)'
            orders = orders.get('deliveryOrders', [])

            if company.iiko_org_id in self.VENUES_WITHOUT_IIKO_PAYMENT_TYPES:
                payments = {}
                for order in orders:
                    for payment in order['payments']:
                        payment = payment['paymentType']
                        if payment['code'] not in payments:
                            payments[payment['code']] = {
                                'type': payment['code'],
                                'name': payment['name']
                            }
                payments = payments.values()
            else:
                payments = self.get_payment_types("iiko", company)

            company.payments = payments
            company.info = {}
            for payment in payments:
                payment = payment['type']
                company.info[payment] = {}
                for status in statuses:
                    info_dict = {
                        "orders_number": 0,
                        "orders_sum": 0,
                        'client_number': 0,
                        'goods_number': 0
                    }
                    company.info[payment][status] = info_dict

            payment_codes = [payment['type'] for payment in payments]
            for order in orders:
                for payment in order['payments']:
                    payment_code = payment['paymentType']['code']
                    if payment_code in payment_codes:
                        if iiko.Order.parse_status(order['status']) in statuses:
                            company.info[payment_code][iiko.Order.parse_status(order['status'])]['orders_number'] += 1
                            company.info[payment_code][iiko.Order.parse_status(order['status'])]['orders_sum'] += payment['sum']
        return companies

    def get(self):
        chosen_type = self.request.get("selected_type")
        chosen_object_type = self.request.get("selected_object_type")
        chosen_company_ids = []
        for company in iiko.CompanyNew.query().fetch():
            if bool(self.request.get(str(company.key.id()))):
                chosen_company_ids.append(company.key.id())

        if not chosen_type:
            chosen_type = 'app'
            chosen_object_type = '0'
        start, end = self.get_date_range()

        statuses = [iiko.Order.CLOSED, iiko.Order.CANCELED, iiko.Order.NOT_APPROVED]
        total = {
            'orders_number': 0,
            'orders_sum': 0,
            'average_orders_sum': 0
        }
        companies = self.get_app_companies_info(start, end, statuses) if chosen_type == "app" \
            else self.get_iiko_companies_info(start, end, statuses)
        if chosen_type == "app":
            for company in companies:
                for payment_key in company.info.keys():
                    total['orders_number'] += company.info[payment_key][iiko.Order.CLOSED]['orders_number']
                    total['orders_sum'] += company.info[payment_key][iiko.Order.CLOSED]['orders_sum']
            total['average_orders_sum'] = round(total['orders_sum'] / total['orders_number'], 2) \
                if total['orders_number'] else 0.0
        values = {
            'companies': companies,
            'chosen_companies': chosen_company_ids,
            'statuses': statuses,
            'statuses_mapping': self.IIKO_STATUS_MAPPING,
            'chosen_type': chosen_type,
            'start': start,
            'end': end,
            'chosen_object_type': chosen_object_type,
            'total': total
        }
        self.render_report('venues', values)

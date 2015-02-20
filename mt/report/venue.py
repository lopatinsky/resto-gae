# -*- coding: utf-8 -*-

__author__ = 'dvpermyakov'

from ..base import BaseHandler
from models import iiko
from methods import iiko_api
from datetime import datetime
from report_methods import suitable_date, PROJECT_STARTING_YEAR
import logging


class VenueReportHandler(BaseHandler):

    IIKO_STATUS_MAPPING = {
        iiko.Order.CLOSED: "CLOSED",
        iiko.Order.CANCELED: "CANCELLED",
        iiko.Order.NOT_APPROVED: "UNCONFIRMED"
    }

    VENUES_WITHOUT_IIKO_PAYMENT_TYPES = [
        iiko.Venue.ORANGE_EXPRESS,  # Оранжеваый эксперсс
        iiko.Venue.COFFEE_CITY   # Coffee and the City
    ]

    def get_payment_types(self, source, venue):
        if source == "app":
            result = []
            for payment in venue.payment_types:
                payment = payment.get()
                result.append({
                    'type': payment.type_id,
                    'name': payment.name
                })
            return result

        elif source == "iiko":
            if venue.source == "iiko":
                return [{
                    'type': payment['code'],
                    'name': payment['name']
                } for payment in iiko_api.get_payment_types(venue.venue_id)['paymentTypes']]
            else:
                return []

    def get_app_venues_info(self, start, end, statuses):
        orders = iiko.Order.query(iiko.Order.date >= start, iiko.Order.date <= end).fetch()
        venues = iiko.Venue.query().fetch()

        venue_ids = {}
        for venue in venues:
            payments = self.get_payment_types("app", venue)
            venue.payments = payments
            venue.info = {}
            for payment in payments:
                payment = payment['type']
                venue.info[payment] = {}
                for status in statuses:
                    info_dict = {
                        "orders_number": 0,
                        "orders_sum": 0
                    }
                    venue.info[payment][status] = info_dict
            venue_ids[venue.venue_id] = venue

        for order in orders:
            venue = venue_ids[order.venue_id]
            if order.status not in statuses:
                continue
            venue.info[int(order.payment_type)][order.status]['orders_number'] += 1
            venue.info[int(order.payment_type)][order.status]['orders_sum'] += order.sum

        return venue_ids.values()

    def get_iiko_venues_info(self, start, end, statuses):
        venues = iiko.Venue.query().fetch()

        for venue in venues:
            orders = iiko_api.get_orders(venue, start, end, status=None)
            orders = orders.get('deliveryOrders', [])

            if venue.venue_id in self.VENUES_WITHOUT_IIKO_PAYMENT_TYPES:
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
                payments = self.get_payment_types("iiko", venue)

            venue.payments = payments
            venue.info = {}
            for payment in payments:
                payment = payment['type']
                venue.info[payment] = {}
                for status in statuses:
                    info_dict = {
                        "orders_number": 0,
                        "orders_sum": 0
                    }
                    venue.info[payment][status] = info_dict

            payment_codes = [payment['type'] for payment in payments]
            for order in orders:
                for payment in order['payments']:
                    payment_code = payment['paymentType']['code']
                    if payment_code in payment_codes:
                        if iiko.Order.parse_status(order['status']) in statuses:
                            venue.info[payment_code][iiko.Order.parse_status(order['status'])]['orders_number'] += 1
                            venue.info[payment_code][iiko.Order.parse_status(order['status'])]['orders_sum'] += payment['sum']
        return venues

    def get(self):
        chosen_type = self.request.get("selected_type")
        chosen_year = self.request.get("selected_year")
        chosen_month = self.request.get_range("selected_month")
        chosen_day = self.request.get_range("selected_day")

        if not chosen_year:
            chosen_year = datetime.now().year
            chosen_month = datetime.now().month
            chosen_day = datetime.now().day
            chosen_type = 'app'
        else:
            chosen_year = int(chosen_year)

        query = iiko.Order.query(iiko.Order.date >= suitable_date(chosen_day, chosen_month, chosen_year, True))
        query = query.filter(iiko.Order.date <= suitable_date(chosen_day, chosen_month, chosen_year, False))
        orders = query.fetch()

        venues = iiko.Venue.query().fetch()
        venue_ids = {}
        for venue in venues:
            venue.order_number = 0
            venue.closed_number = 0
            venue.closed_sum = 0
            venue.cancel_number = 0
            venue.cancel_sum = 0
            venue.delivery = 0
            venue.card = 0
            venue_ids[venue.venue_id] = venue
        for order in orders:
            venue = venue_ids[order.venue_id]
            venue.order_number += 1
            if order.status == iiko.Order.CLOSED:
                venue.closed_number += 1
                venue.closed_sum += order.sum
            elif order.status == iiko.Order.CANCELED:
                venue.cancel_number += 1
                venue.cancel_sum += order.sum
            if order.is_delivery:
                venue.delivery += 1
            if order.payment_type == order.CARD:
                venue.card += 1

        start = suitable_date(chosen_day, chosen_month, chosen_year, True)
        end = suitable_date(chosen_day, chosen_month, chosen_year, False)

        statuses = [iiko.Order.CLOSED, iiko.Order.CANCELED, iiko.Order.NOT_APPROVED]
        values = {
            'venues': self.get_app_venues_info(start, end, statuses) if chosen_type == "app"
            else self.get_iiko_venues_info(start, end, statuses),
            'statuses': statuses,
            'statuses_mapping': self.IIKO_STATUS_MAPPING,
            'start_year': PROJECT_STARTING_YEAR,
            'end_year': datetime.now().year,
            'chosen_type': chosen_type,
            'chosen_year': chosen_year,
            'chosen_month': chosen_month,
            'chosen_day': chosen_day
        }
        self.render('reported_venues.html', **values)

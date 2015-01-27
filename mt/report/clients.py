__author__ = 'dvpermyakov'

from ..base import BaseHandler
from datetime import datetime
from models import iiko
from report_methods import suitable_date, PROJECT_STARTING_YEAR
import logging


class ClientsReportHandler(BaseHandler):

    @staticmethod
    def get_clients_info(chosen_year=0, chosen_month=0, chosen_day=0, venue_id=None):
        logging.info('venue_id: %s' % venue_id)
        query = iiko.Order.query(iiko.Order.date >= suitable_date(chosen_day, chosen_month, chosen_year, True))
        query = query.filter(iiko.Order.date <= suitable_date(chosen_day, chosen_month, chosen_year, False))
        if venue_id:
            query = query.filter(iiko.Order.venue_id == venue_id)

        clients = {}
        for order in query.fetch():
            client = order.customer.get()
            if client.key.id() not in clients:
                if order.status == iiko.Order.CLOSED:
                    client.order_number = 1
                    client.total_sum = order.sum
                    client.cancelled = 0
                    client.cancelled_sum = 0
                    if order.payment_type == iiko.Order.CARD:
                        client.card = 1
                    else:
                        client.card = 0
                elif order.status == iiko.Order.CANCELED:
                    client.order_number = 0
                    client.total_sum = 0
                    client.cancelled = 1
                    client.cancelled_sum = order.sum
                    client.card = 0
                if order.status == iiko.Order.CLOSED or order.status == iiko.Order.CANCELED:
                    clients[client.key.id()] = client
            else:
                client = clients[client.key.id()]
                if order.status == iiko.Order.CLOSED:
                    client.order_number += 1
                    client.total_sum += order.sum
                    if order.payment_type == iiko.Order.CARD:
                        client.card = 1
                elif order.status == iiko.Order.CANCELED:
                    client.cancelled += 1
                    client.cancelled_sum += order.sum
        clients = clients.values()
        total = {
            'order_number': sum(client.order_number for client in clients),
            'total_sum': sum(client.total_sum for client in clients),
            'cancelled': sum(client.cancelled for client in clients),
            'cancelled_sum': sum(client.cancelled_sum for client in clients)
        }

        return clients, total

    def get(self):
        venue_id = self.request.get("selected_venue")
        chosen_year = self.request.get_range("selected_year")
        chosen_month = self.request.get_range("selected_month")
        chosen_day = self.request.get_range("selected_day")
        if not chosen_year:
            chosen_month = 0
        if not chosen_month:
            chosen_day = 0
        if not venue_id:
            venue_id = 0
            chosen_year = datetime.now().year
            chosen_month = datetime.now().month
            chosen_day = datetime.now().day
        if venue_id == '0':
            venue_id = None
        clients, total = self.get_clients_info(chosen_year, chosen_month, chosen_day, venue_id)
        values = {
            'venues': iiko.Venue.query().fetch(),
            'clients': clients,
            'total': total,
            'chosen_venue': iiko.Venue.venue_by_id(venue_id) if venue_id else None,
            'start_year': PROJECT_STARTING_YEAR,
            'end_year': datetime.now().year,
            'chosen_year': chosen_year,
            'chosen_month': chosen_month,
            'chosen_day': chosen_day
        }
        self.render('reported_clients.html', **values)
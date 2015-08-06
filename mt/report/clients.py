from methods.iiko.history import get_history

__author__ = 'dvpermyakov'

from ..base import BaseHandler
from datetime import datetime
from models import iiko
from report_methods import suitable_date, PROJECT_STARTING_YEAR
import logging


class ClientsReportHandler(BaseHandler):

    def get_iiko_clients_info(self, clients, start, end):

        for client in clients.values():
            orders = get_history(client.customer_id, client.venue_id)
            orders = orders['historyOrders']
            for order in orders:
                logging.info(order)
                if order.get('status'):
                    if iiko.Order.parse_status(order['status']) == iiko.Order.CLOSED:
                        client.order_number += 1
                        client.total_sum += order['sum']
                    elif iiko.Order.parse_status(order['status']) == iiko.Order.CANCELED:
                        client.cancelled += 1
                        client.cancelled_sum += order['sum']
        clients = clients.values()
        total = {
            'order_number': sum(client.order_number for client in clients),
            'card_order': sum(client.card for client in clients),
            'total_sum': sum(client.total_sum for client in clients),
            'cancelled': sum(client.cancelled for client in clients),
            'cancelled_sum': sum(client.cancelled_sum for client in clients)
        }

        return clients, total

    def get_app_clients_info(self, orders, clients):

        for order in orders:
            client = clients[order.client_id]
            if order.status == iiko.Order.CLOSED:
                client.order_number += 1
                client.total_sum += order.sum
                if order.payment_type == iiko.Order.CARD:
                    client.card += 1
            elif order.status == iiko.Order.CANCELED:
                client.cancelled += 1
                client.cancelled_sum += order.sum
        clients = clients.values()
        total = {
            'order_number': sum(client.order_number for client in clients),
            'card_order': sum(client.card for client in clients),
            'total_sum': sum(client.total_sum for client in clients),
            'cancelled': sum(client.cancelled for client in clients),
            'cancelled_sum': sum(client.cancelled_sum for client in clients)
        }
        return clients, total

    def get_clients_info(self, chosen_year=0, chosen_month=0, chosen_day=0, org_id=None, chosen_type='app'):
        start = suitable_date(chosen_day, chosen_month, chosen_year, True)
        end = suitable_date(chosen_day, chosen_month, chosen_year, False)
        query = iiko.Order.query(iiko.Order.date >= start, iiko.Order.date <= end)
        if org_id:
            query = query.filter(iiko.Order.venue_id == org_id)
        orders = query.fetch()

        clients = {}
        for order in orders[:]:
            if not order.customer:
                orders.remove(order)
                continue
            client = order.customer.get()
            order.client_id = client.customer_id
            if client.customer_id not in clients:
                client.order_number = 0
                client.total_sum = 0
                client.cancelled = 0
                client.cancelled_sum = 0
                client.card = 0
                client.venue_id = order.venue_id
                clients[client.customer_id] = client

        if chosen_type == 'app':
            return self.get_app_clients_info(orders, clients)
        else:
            return self.get_iiko_clients_info(clients, start, end)

    def get(self):
        chosen_type = self.request.get("selected_type")
        org_id = self.request.get("selected_company")
        chosen_year = self.request.get_range("selected_year")
        chosen_month = self.request.get_range("selected_month")
        chosen_day = self.request.get_range("selected_day")
        if not chosen_year:
            chosen_month = 0
        if not chosen_month:
            chosen_day = 0
        if not org_id:
            org_id = '0'
            chosen_type = 'app'
            chosen_year = datetime.now().year
            chosen_month = datetime.now().month
            chosen_day = datetime.now().day
        if org_id == '0':
            org_id = None
        clients, total = self.get_clients_info(chosen_year, chosen_month, chosen_day, org_id, chosen_type)
        values = {
            'companies': iiko.CompanyNew.query().fetch(),
            'clients': clients,
            'total': total,
            'chosen_company': iiko.CompanyNew.get_by_iiko_id(org_id),
            'start_year': PROJECT_STARTING_YEAR,
            'end_year': datetime.now().year,
            'chosen_year': chosen_year,
            'chosen_month': chosen_month,
            'chosen_day': chosen_day,
            'chosen_type': chosen_type
        }
        self.render('reported_clients.html', **values)
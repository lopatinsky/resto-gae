# coding=utf-8

from .base import BaseReportHandler
from models import iiko
import logging
from methods.iiko.history import get_history

__author__ = 'dvpermyakov'



class ClientsReportHandler(BaseReportHandler):
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
                if order.payment_type == iiko.PaymentType.CARD:
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

    def get_clients_info(self, start, end, org_id=None, chosen_type='app'):
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
        if not chosen_type:
            chosen_type = 'app'
            org_id = None
        start, end = self.get_date_range()
        clients, total = self.get_clients_info(start, end, org_id, chosen_type)
        values = {
            'companies': iiko.CompanyNew.query().fetch(),
            'clients': clients,
            'total': total,
            'chosen_company': iiko.CompanyNew.get_by_iiko_id(org_id),
            'start': start,
            'end': end,
            'chosen_type': chosen_type
        }
        self.render_report('clients', values)

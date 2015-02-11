__author__ = 'dvpermyakov'

from ..base import BaseHandler
from datetime import datetime, timedelta
from report_methods import suitable_date, PROJECT_STARTING_YEAR
from models import iiko
from methods import iiko_api
from random import randint
import calendar


class RepeatedOrdersReportHandler(BaseHandler):

    def get_app_repeated_orders(self, chosen_year, chosen_month, chosen_day, venue_id):
        days = []
        total = {
            'new_number': 0,
            'old_number': 0,
            'new_sum': 0,
            'old_sum': 0
        }
        for day in range(1, calendar.monthrange(chosen_year, chosen_month)[1] + 1):
            if chosen_day != 0:
                if day != chosen_day:
                    continue
            new_number = 0
            old_number = 0
            new_sum = 0
            old_sum = 0
            start = suitable_date(day, chosen_month, chosen_year, True)
            end = suitable_date(day, chosen_month, chosen_year, False)
            query = iiko.Order.query(iiko.Order.date >= start, iiko.Order.date <= end,
                                     iiko.Order.status == iiko.Order.CLOSED)
            if venue_id:
                query.filter(iiko.Order.venue_id == venue_id)
                query = query.filter(iiko.Order.venue_id == venue_id)
            for order in query.fetch():
                customer_key = order.customer
                first_order = iiko.Order.query(iiko.Order.customer == customer_key,
                                               iiko.Order.status == iiko.Order.CLOSED)\
                    .order(iiko.Order.date).get()
                if first_order.key.id() == order.key.id():
                    new_number += 1
                    new_sum += order.sum
                else:
                    old_number += 1
                    old_sum += order.sum
            days.append({
                'day': day,
                'new_number': new_number,
                'old_number': old_number,
                'new_sum': new_sum,
                'old_sum': old_sum
            })
            total['new_number'] += new_number
            total['old_number'] += old_number
            total['new_sum'] += new_sum
            total['old_sum'] += old_sum
        return days, total

    def get_iiko_repeated_orders(self, chosen_year, chosen_month, chosen_day, venue_id, chosen_client_number):
        venue = iiko.Venue.venue_by_id(venue_id)
        if not venue:
            return [], {}
        day_orders = []
        clients_id = []
        for day in range(1, calendar.monthrange(chosen_year, chosen_month)[1] + 1):
            if chosen_day != 0:
                if day != chosen_day:
                    continue
            start = suitable_date(day, chosen_month, chosen_year, True)
            end = suitable_date(day, chosen_month, chosen_year, False)
            orders = iiko_api.get_orders(venue, start, end, status='CLOSED')
            orders = orders.get('deliveryOrders', [])
            day_orders.append(orders)
            for order in orders:
                if order['customerId'] not in clients_id:
                    clients_id.append(order['customerId'])

        if len(clients_id) > chosen_client_number:
            new_clients_id = []
            while len(new_clients_id) < chosen_client_number:
                index = randint(0, len(clients_id) - 1)
                new_clients_id.append(clients_id[index])
                del clients_id[index]
            clients_id = new_clients_id

        first_orders = {}
        for client_id in clients_id:
            orders = iiko_api.get_history(client_id, venue_id)
            orders = orders['historyOrders']
            for order in orders:
                if not first_orders.get(client_id):
                    first_orders[client_id] = datetime.strptime(order['date'][:10], '%Y-%m-%d')
                else:
                    order_date = datetime.strptime(order['date'][:10], '%Y-%m-%d')
                    if first_orders[client_id] > order_date:
                        first_orders[client_id] = order_date

        days = []
        total = {
            'new_number': 0,
            'old_number': 0,
            'new_sum': 0,
            'old_sum': 0
        }
        for day, orders in enumerate(day_orders):
            new_number = 0
            old_number = 0
            new_sum = 0
            old_sum = 0
            for order in orders:
                if order['customerId'] not in clients_id:
                    continue
                order_time = datetime.strptime(order['deliveryDate'][:10], '%Y-%m-%d')
                if abs(order_time - first_orders[order['customerId']]) < timedelta(minutes=1):
                    new_number += 1
                    new_sum += order['sum']
                else:
                    old_number += 1
                    old_sum += order['sum']
            days.append({
                'day': day,
                'new_number': new_number,
                'old_number': old_number,
                'new_sum': new_sum,
                'old_sum': old_sum
            })
            total['new_number'] += new_number
            total['old_number'] += old_number
            total['new_sum'] += new_sum
            total['old_sum'] += old_sum
        return days, total

    def get(self):
        chosen_type = self.request.get("selected_type")
        venue_id = self.request.get("selected_venue")
        chosen_year = self.request.get_range("selected_year")
        chosen_month = self.request.get_range("selected_month")
        chosen_day = self.request.get_range("selected_day")
        chosen_client_number = self.request.get_range("selected_client_number")
        if not chosen_year:
            chosen_month = 0
        if not chosen_month:
            chosen_day = 0
        if not venue_id:
            chosen_type = 'app'
            chosen_year = datetime.now().year
            chosen_month = datetime.now().month
            chosen_day = 0
        if venue_id == '0':
            venue_id = None

        if chosen_type == 'app':
            days, total = self.get_app_repeated_orders(chosen_year, chosen_month, chosen_day, venue_id)
        else:
            days, total = self.get_iiko_repeated_orders(chosen_year, chosen_month, chosen_day, venue_id,
                                                        chosen_client_number)

        values = {
            'venues': iiko.Venue.query().fetch(),
            'days': days,
            'total': total,
            'chosen_type': chosen_type,
            'chosen_client_number': chosen_client_number,
            'chosen_venue': iiko.Venue.venue_by_id(venue_id) if venue_id else None,
            'start_year': PROJECT_STARTING_YEAR,
            'end_year': datetime.now().year,
            'chosen_year': chosen_year,
            'chosen_month': chosen_month,
            'chosen_day': chosen_day
        }
        self.render('reported_repeated_orders.html', **values)
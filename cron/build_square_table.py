# coding=utf-8

from datetime import timedelta, datetime
from webapp2 import RequestHandler
from methods.times import timestamp
from models.iiko import Order, CompanyNew
from models.square_table import JsonStorage


class BuildSquareTableHandler(RequestHandler):
    def get_orders_info(self, orders, begin, end):
        goods_number = 0
        order_number = len(orders)
        order_sum = 0
        client_ids = []
        for order in orders:
            goods_number += len(order.items)
            order_sum += order.sum
            if not order.customer.id() in client_ids:
                client_ids.append(order.customer.id())

        return {
            "goods_number": goods_number,
            "order_number": order_number,
            "order_sum": order_sum,
            "client_number": len(client_ids),
            "begin": timestamp(begin),
            "end": timestamp(end - timedelta(minutes=1))
        }

    def get_square_table(self, company):
        orders = Order.query(Order.status == Order.CLOSED, Order.venue_id == company.iiko_org_id).fetch()

        if not orders:
            return None

        clients = []
        for order in orders:
            client = order.customer.get()
            client.first_order_time = None
            clients.append(client)
        clients_map = {c.key.id(): c for c in clients}

        for order in orders:
            client = clients_map[order.customer.id()]
            if not client.first_order_time or client.first_order_time > order.date:
                client.first_order_time = order.date

        clients = sorted(clients, key=lambda client: client.first_order_time)
        start_time = clients[0].first_order_time
        start_time = start_time.replace(hour=0, minute=0)

        def _week_number(dt):
            return (dt - start_time).days / 7

        def _week_start(number):
            return start_time + timedelta(days=7 * number)

        weeks_count = _week_number(datetime.now()) + 1

        orders_square = []
        for i in xrange(weeks_count):
            orders_row = []
            for j in xrange(weeks_count):
                orders_row.append([])
            orders_square.append(orders_row)

        client_week = {}
        for client in clients:
            client_week[client.key.id()] = _week_number(client.first_order_time)

        for order in orders:
            row = client_week[order.customer.id()]
            column = _week_number(order.date)
            orders_square[row][column].append(order)

        return [
            [
                self.get_orders_info(cell, begin=_week_start(i), end=_week_start(i+1))
                for i, cell in enumerate(row)
            ]
            for row in orders_square
        ]

    def get(self):
        companies = CompanyNew.query().fetch()
        companies_dict = {}
        for company in companies:
            companies_dict[company.iiko_org_id] = self.get_square_table(company)

        JsonStorage.save("square_table", companies_dict)

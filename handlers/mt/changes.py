# coding=utf-8
from .base import BaseHandler
from models.iiko import Order


class ChangeLogFindOrderHandler(BaseHandler):
    def get(self):
        last_updated = Order.query().order(-Order.updated).fetch(10)
        self.render('changelog/find_order.html', orders=last_updated)

    def post(self):
        number = self.request.get('number')
        order_by_id = Order.order_by_id(number)
        if order_by_id:
            orders = [order_by_id]
        else:
            orders = Order.query(Order.number == number).fetch()
        if len(orders) == 1:
            self.redirect_to("view_changelog", order_id=orders[0].order_id)
        else:
            self.render('changelog/find_order.html', orders=orders, search=True)


class ViewChangeLogsHandler(BaseHandler):
    def get(self, order_id):
        order = Order.order_by_id(order_id)
        changes = order.get_change_logs()
        self.render('/changelog/view.html', order=order, changes=changes)

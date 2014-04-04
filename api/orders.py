# coding=utf-8
import json
import datetime
import webapp2
import iiko
import base

__author__ = 'quiker'


class PlaceOrderRequestHandler(base.BaseHandler):
    """ /api/venue/%s/order/new """
    def get(self, venue_id):
        customer = iiko.Customer()
        customer.phone = '+79637174789'
        customer.name = u'Сергей Пронин'

        order = iiko.Order()
        order.sum = 340
        order.date = datetime.datetime.utcnow() + datetime.timedelta(hours=4)
        order.venue_id = venue_id
        order.items = [
            {
                'id': 'b9c6077c-414b-4023-a061-e12d763eb9bd',
                'name': 'Jagermeister',
                'amount': '1'
            },
            {
                'id': 'd481b6dd-2966-4090-8628-22e4e7842277',
                'name': 'Campari',
                'amount': '1'
            }
        ]

        result = iiko.place_order(order, customer)
        result['status'] = result['status'].encode('utf-8')

        self.render_json(result)

    def post(self, venue_id):
        name = self.request.get('name')
        phone = self.request.get('phone')

        customer = iiko.Customer.customer_by_phone(phone)
        if not customer:
            customer = iiko.Customer()
            customer.phone = phone
            customer.name = name
            customer.put()

        order = iiko.Order()
        order.sum = self.request.get('sum')
        order.date = datetime.datetime.fromtimestamp(self.request.get('date'))
        order.venue_id = venue_id
        order.items = self.request.get('items')
        order.customer = customer.key

        result = iiko.place_order(order, customer)

        if not customer.customer_id:
            customer.customer_id = 'd1e4df89-8a4a-40eb-aa8c-e3edfc143a3d'
            customer.put()

        order.order_id = result['orderId']
        order.number = result['number']
        order.status = result['status'].encode('utf-8')

        order.put()

        self.render_json({
            'customerId': customer.customer_id,
            'order': order.to_dict()
        })


class OrderInfoRequestHandler(base.BaseHandler):
    """ /api/venue/%s/order/%s """
    def get(self, venue_id, order_id):
        order = iiko.Order.order_by_id(order_id)

        self.render_json({
            'order': iiko.order_info1(order_id, venue_id)
        })
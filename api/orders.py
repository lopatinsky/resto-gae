# coding=utf-8
import json
import logging
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
        order.order_id = result['orderId']
        order.number = result['number']
        order.set_status(result['status'])

        order.put()

        self.render_json(result)

    def post(self, venue_id):
        logging.info(self.request.body)

        name = self.request.get('name')
        phone = self.request.get('phone')
        customer_id = self.request.get('customer_id')

        customer = iiko.Customer.customer_by_customer_id(customer_id)
        if not customer:
            customer = iiko.Customer()
            customer.phone = phone
            customer.name = name
            customer.customer_id = customer_id
            customer.put()

        order = iiko.Order()
        order.sum = int(self.request.get('sum'))
        order.date = datetime.datetime.fromtimestamp(int(self.request.get('date')))
        order.venue_id = venue_id
        order.items = json.loads(self.request.get('items'))
        order.customer = customer.key

        result = iiko.place_order(order, customer)

        order.order_id = result['orderId']
        order.number = result['number']
        order.set_status(result['status'])

        order.put()

        self.render_json({
            'customerId': customer.customer_id,
            'order': order.to_dict()
        })


class VenueOrderInfoRequestHandler(base.BaseHandler):
    """ /api/venue/%s/order/%s """
    def get(self, venue_id, order_id):
        order = iiko.Order.order_by_id(order_id)

        result = iiko.order_info1(order_id, venue_id)
        result['status'] = result['status'].replace(u'Новая', u'Подтвержден')
        result['status'] = result['status'].replace(u'Закрыта', u'Закрыт')

        self.render_json({
            'order': result
        })


class OrderInfoRequestHandler(base.BaseHandler):
    """ /api/order/%s """
    def get(self, order_id):
        order = iiko.Order.order_by_id(order_id)

        result = iiko.order_info(order)
        order.set_status(result['status'])
        order.put()

        self.render_json({
            'order': order.to_dict()
        })
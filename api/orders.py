# coding=utf-8
import json
import logging
import datetime
import webapp2
import iiko
import base
from iiko.requests import get_iiko_net_payments, create_order_with_bonus

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
        logging.info(self.request.POST)

        name = self.request.get('name')
        phone = self.request.get('phone')
        customer_id = self.request.get('customer_id')
        delivery_type = self.request.get('deliveryType', 0)
        payment_type = self.request.get('paymentType')
        address = self.request.get('address')
        comment = self.request.get('comment')

        customer = iiko.Customer.customer_by_customer_id(customer_id)
        if not customer:
            customer = iiko.Customer()
            customer.phone = phone
            customer.name = name
            if customer_id:
                customer.customer_id = customer_id
            customer.put()


        order = iiko.Order()
        order.sum = float(self.request.get('sum'))
        order.date = datetime.datetime.fromtimestamp(int(self.request.get('date')))
        order.venue_id = venue_id
        order.items = json.loads(self.request.get('items'))
        order.customer = customer.key
        order.comment = comment
        order.is_delivery = int(delivery_type) == 0
        if order.is_delivery:
            if not address:
                self.abort(400)
            try:
                order.address = json.loads(address)
            except:
                self.abort(400)

        result = iiko.place_order(order, customer, payment_type)
        if 'code' in result.keys():
            self.response.set_status(500)
            return self.render_json(result)
        if not customer_id:
            customer.customer_id = result['customerId']
            customer.put()

        order.order_id = result['orderId']
        order.number = result['number']
        order.set_status(result['status'])

        order.put()

        resp = {
            'customer_id': customer.customer_id,
            'order': {'order_id': order.order_id,
                      'status': order.status,
                      'items': order.items,
                      'sum': order.sum,
                      'number': order.number,
                      'venue_id': order.venue_id,
                      'address': order.address,}
        }

        self.render_json(resp)


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
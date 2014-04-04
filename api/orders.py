# coding=utf-8
import json
import datetime
import webapp2
import iiko

__author__ = 'quiker'


class PlaceOrderRequestHandler(webapp2.RequestHandler):
    """ /api/order/new """
    def get(self):
        customer = iiko.Customer()
        customer.phone = '+79637174789'
        customer.name = u'Сергей Пронин'

        order = iiko.Order()
        order.sum = 340
        order.date = datetime.datetime.utcnow() + datetime.timedelta(hours=4)
        order.venue_id = '95e4a970-b4ea-11e3-8bac-50465d4d1d14'
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

        self.response.headers['Content-Type'] = 'application/json'
        self.response.out.write(json.dumps(result))

    def post(self):
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
        order.venue_id = self.request.get('venue_id')
        order.items = self.request.get('items')
        order.customer = customer.key

        result = iiko.place_order(order, customer)

        order.order_id = result['orderId']
        order.number = result['number']
        order.status = result['status'].encode('utf-8')
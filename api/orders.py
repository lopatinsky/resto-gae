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
        delivery_type = self.request.get('deliveryType', 0)
        address = self.request.get('address')

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
        order.is_delivery = int(delivery_type) == 0
        if order.is_delivery:
            if not address:
                self.abort(400)
            try:
                order.address = json.loads(address)
            except:
                self.abort(400)

        result = iiko.place_order(order, customer)
        if 'error' in result.keys():
            return result
        if not customer_id:
            customer.customer_id = result['customerId']
            customer.put()

        order.order_id = result['orderId']
        order.number = result['number']
        order.set_status(result['status'])

        order.put()

        resp = {
            'customerId': customer.customer_id,
            'order': order.to_dict()
        }

        """
        {"restaurantId":"95e4a970-b4ea-11e3-8bac-50465d4d1d14","deliveryTerminalId":"dd121a59-a43e-0690-0144-f47bced50158",
        "customer":{"name":"\u0420\u0443\u0441\u0442\u0435\u043c \u0442\u0435\u0441\u0442","phone":"+79164470722", id:""},

        "order":{"date":"2014-08-19 20:00:00","isSelfService":"1",
          "paymentItems":
              [{"paymentType":{"id":"bf2fd2db-cc75-46fa-97af-4f9dc68bb34b","code":333,"
                 name":"\u0411\u0430\u043d\u043a\u043e\u0432\u0441\u043a\u0438\u0435 \u043a\u0430\u0440\u0442\u044b"},
                 "sum":995,"isProcessedExternally":1}],
          "phone":"+79164470722",
                 "items":[{"id":"abf48832-26c0-4fc8-8776-277713aed60d",
                 "name":"Bordeaux Blanc Chateau \u0431\u0435\u043b150\u043c\u043b","amount":"2"},
                 {"id":"0f686752-b343-4f08-8a4d-69146bdfc1cb",
                 "name":"\u0431\u0435\u0444-\u0441\u0442\u0440\u043e\u0433\u0430\u043d\u043e\u0432","amount":"1"}],

             "address":{"city":"\u041c\u043e\u0441\u043a\u0432\u0430",
             "street":"\u041a\u0440\u0430\u0441\u043d\u0430\u044f \u043f\u043b\u043e\u0449\u0430\u0434\u044c",
             "home":"1","housing":"1","apartment":"12","comment":"\u043a\u043e\u043c\u0435\u043d\u0442\u0430\u0440\u0438\u0439"}}
        }
        """
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
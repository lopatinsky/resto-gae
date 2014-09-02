# coding=utf-8
import json
import logging
import datetime
import time
import iiko
import base
from iiko.requests import tie_card, create_pay, pay_by_card
from iiko.model import PaymentType

__author__ = 'quiker'

LOGIN = 'empatika_autopay-api'
PASSWORD = 'empatika_autopay'


class PlaceOrderRequestHandler(base.BaseHandler):
    """ /api/venue/%s/order/new """

    def post(self, venue_id):
        logging.info(self.request.POST)

        name = self.request.get('name')
        phone = self.request.get('phone')
        customer_id = self.request.get('customer_id')
        delivery_type = self.request.get('deliveryType', 0)
        payment_type = self.request.get('paymentType')
        address = self.request.get('address')
        comment = self.request.get('comment')
        sum = self.request.get('sum');
        binding_id = self.request.get('binding_id')
        alpha_client_id = self.request.get('alpha_client_id')

        customer = iiko.Customer.customer_by_customer_id(customer_id)
        if not customer:
            customer = iiko.Customer()
            customer.phone = phone
            customer.name = name
            if customer_id:
                customer.customer_id = customer_id
            customer.put()

        # TODO do it right
        # Sorry, Misha, shame on me =(
        if payment_type == '2':
            tie_result = tie_card(LOGIN, PASSWORD, sum * 100, int(time.time()), 'returnUrl',  alpha_client_id, 'MOBILE')
            logging.info("registration")
            logging.info(str(tie_result))
            if 'errorCode' not in tie_result.keys() or str(tie_result['errorCode']) == '0':
                order_id = tie_result['orderId']
                create_result = create_pay(LOGIN, PASSWORD, binding_id, order_id)
                logging.info("block")
                logging.info(str(create_result))
                if 'errorCode' not in create_result.keys() or str(create_result['errorCode']) == '0':
                    pay_result = pay_by_card(LOGIN, PASSWORD, order_id, 0)
                    logging.info("pay")
                    logging.info(str(pay_result))
                    if 'errorCode' not in pay_result.keys() or str(pay_result['errorCode']) == '0':
                        pass
                    else:
                       self.abort(400)
                else:
                    self.abort(400)
            else:
                self.abort(400)


        order = iiko.Order()
        order.sum = float(sum)
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
                      'address': order.address,},
            'error_code' : 0,
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
# -*- coding: utf-8 -*-

__author__ = 'dvpermyakov'

import webapp2
from methods import parse_com
from models import iiko, specials
import logging

VENUE_ID = 'a9d16dff-7680-43f1-b1a1-74784bc75f60'


class SendPushesHandler(webapp2.RequestHandler):
    def post(self):

        orders = iiko.Order.query(iiko.Order.venue_id == VENUE_ID).fetch()
        order_ids = []
        customer_ids = []
        for order in orders:
            customer = order.customer.get()
            if hasattr(customer, 'customer_id'):
                if customer.customer_id not in customer_ids:
                    customer_ids.append(customer.customer_id)
                    order_ids.append(order.order_id)

        order_ids.append('74719eda-0dc1-4987-9e88-bec7f1e6565f')
        order_ids.append('589174fa-62fd-4f93-b368-10d94f758a05')

        data = {
            'order_id': u'',
            'order_status': u'',
            'action': 'com.empatika.iiko'
        }
        message = u'Ролл РОК-Н-РОЛЛ в подарок при заказе от 500 рублей. Только сегодня.'

        result = parse_com.send_push(channel=None, channels=["order_%s" % order_id for order_id in order_ids],
                                     alert=message, data=data)
        logging.info(result)
        for order_id in order_ids:
            spam = specials.Notification(order_id=order_id, type=specials.Notification.PUSH_NOTIFICATION)
            spam.put()
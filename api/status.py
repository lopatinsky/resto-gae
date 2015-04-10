# coding=utf-8

import logging
from api.base import BaseHandler
from models.iiko import Order, DeliveryTerminal
from methods import iiko_api
import json


# TODO: existing of goods
# TODO: new endpoint (possibility to deliver)
# TODO: check time
class OrdersStatusHandler(BaseHandler):
    """ /api/status """

    def post(self):
        status_list = list()
        # parse data
        logging.info(self.request.get('json'))
        arr = json.loads(self.request.get('json'))

        for item in arr["orders"]:
            # get ids and info
            delivery_terminal_id = item['venue_id']
            delivery_terminal = DeliveryTerminal.get_by_id(delivery_terminal_id)
            if not delivery_terminal:
                # old version: got organization id instead of DT id
                delivery_terminal = DeliveryTerminal.get_any(delivery_terminal_id)
                delivery_terminal_id = delivery_terminal.key.id()
            order_id = item['order_id']

            order_info = iiko_api.order_info1(order_id, delivery_terminal.iiko_organization_id)
            if 'httpStatusCode' not in order_info:
                address = delivery_terminal.address
                name = delivery_terminal.name

                # make dict
                status_list.append({
                    'order_id': order_id,
                    'venue_id': delivery_terminal_id,
                    'status': Order.parse_status(order_info['status']),
                    'address': address,
                    'name': name,
                    'createdTime': order_info['createdTime']
                })
            else:
                logging.warning('order %s not found' % order_id)
        self.render_json({"orders": status_list})

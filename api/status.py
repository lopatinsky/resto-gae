# coding=utf-8

import logging
from api.base import BaseHandler
from models.iiko import Order
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
            venue_id = item['venue_id']
            order_id = item['order_id']

            order_info = iiko_api.order_info1(order_id, venue_id)
            if 'httpStatusCode' not in order_info:
                venue = Venue.venue_by_id(venue_id)
                address = venue.address
                name = venue.name

                # make dict
                status_list.append({
                    'order_id': order_id,
                    'venue_id': venue_id,
                    'status': Order.parse_status(order_info['status']),
                    'address': address,
                    'name': name,
                    'createdTime': order_info['createdTime']
                })
            else:
                logging.warning('order %s not found' % order_id)
        self.render_json({"orders": status_list})

import logging
from api.base import BaseHandler
import iiko
import json

__author__ = 'mihailnikolaev'


class StatusRequestHandler(BaseHandler):
    """ /api/status/%s """
    status_list = list()

    def get(self, json_orders):
        self.status_list = list()
        #parce data
        arr = json.loads(json_orders)

        for item in arr["orders"]:
            #get ids and info
            venue_id = item['venue_id']
            order_id = item['order_id']
            order_info = iiko.order_info1(order_id, venue_id)
            venue_info = iiko.Venue.venue_by_id(venue_id)

            #make dict
            self.status_list.append({
                'order_id': order_id,
                'venue_id': venue_id,
                'status': order_info['status'],
                'address': venue_info.address,
                'name': venue_info.name,
                'createdTime': iiko.order_info1(order_id, venue_id)['createdTime']
            })
        self.render_json({"orders": self.status_list})
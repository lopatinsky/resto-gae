import logging
from api.base import BaseHandler
from iiko.model import Order
import iiko
import json

__author__ = 'mihailnikolaev'

#TODO: existing of goods
#TODO: new endpoint (possibility to deliver)
#TODO: check time
class StatusRequestHandler(BaseHandler):
    """ /api/status """
    status_list = list()

    def post(self):
        self.status_list = list()
        #parce data
        print self.request.get('json')
        arr = json.loads(self.request.get('json'))

        for item in arr["orders"]:
            #get ids and info
            venue_id = item['venue_id']
            order_id = item['order_id']

            order_info = iiko.order_info1(order_id, venue_id)
            venues = iiko.get_venues()
            print venues
            address = ""
            name = ""
            #get venue
            for venue in venues:
                if venue.venue_id == venue_id:
                    address = venue.address
                    name = venue.name
            order = Order()
            order.order_id = order_id
            order.set_status(order_info['status'])
            order.put()
            #make dict
            self.status_list.append({
                'order_id': order_id,
                'venue_id': venue_id,
                'status': order.status,
                'address': address,
                'name': name,
                'createdTime': iiko.order_info1(order_id, venue_id)['createdTime']
            })
            order.key.delete()
        self.render_json({"orders": self.status_list})
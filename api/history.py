import json
import logging
import webapp2
from api.base import BaseHandler
import iiko
import time
from datetime import datetime

__author__ = 'Rustemr'


class HistoryRequestHandler(BaseHandler):
    """ /api/history """
    overall_history = list()

    def get(self):
        client_id = self.request.get('client_id')
        org_id = self.request.get('organisation_id')
        for venue in iiko.get_venues(org_id):
            logging.info(str(venue))
            history = iiko.get_history(client_id, venue.venue_id)
            orders_history = list()
            self.overall_history = list()
            if not 'historyOrders' in history or not history['historyOrders']:
                pass
            else:
                for order in history['historyOrders']:
                    items_list = list()
                    for order_items in order['items']:
                        items_list.append({
                            'sum': order_items['sum'],
                            'amount': order_items['amount'],
                            'name': order_items['name'],
                            'modifiers': order_items['modifiers'],
                            'id': order_items['id'],
                        })

                    # current_time = iiko.order_info1(order['orderId'], venue.venue_id)
                    # logging.info(current_time)

                    address = {}
                    if order['address']:
                        address = {'city': order['address']['city'],
                                         'street': order['address']['street'],
                                         'home': order['address']['home'],
                                         'apartment': order['address']['apartment'],
                                         'housing': order['address']['housing'],
                                         'entrance': order['address']['entrance'],
                                         'floor': order['address']['floor'], }

                    orders_history.append({
                        'self': order['isSelfService'],
                        'order_id': order['orderId'],
                        'number': order['number'],
                        'address': address,
                        # 'order_organization':order['organizationId'],
                        'date': time.mktime(datetime.strptime(order['date'], "%Y-%m-%d %H:%M:%S").timetuple()),
                        # 'order_current_date': current_time,
                        'phone': order['phone'],
                        'discount': order['discount'],
                        'sum': order['sum'],
                        'items': items_list,
                        'venue_id': venue.venue_id,
                    })
            self.overall_history.append({
                'venue_id': venue.venue_id,
                'address': venue.address,
                'name': venue.name,
                'local_history': orders_history
            })

        self.render_json({'history': self.overall_history})



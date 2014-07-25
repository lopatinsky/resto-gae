import json
import webapp2
from api.base import BaseHandler
import iiko

__author__ = 'Rustemr'


class HistoryRequestHandler(BaseHandler):
    """ /api/history """
    overall_history = list()

    def get(self):
        client_id = self.request.get('client_id')
        org_id = self.request.get('organisation_id')
        for venue in iiko.get_venues(org_id):
            # client_id = client_id[:8] + '-' + client_id[8:12] + '-' + client_id[12:16] + '-' + client_id[16:20] + '-' + \
            #                 client_id[20:]
            history = iiko.get_history(client_id, venue.venue_id)
            orders_history = list()
            if not history:
                orders_history.append({
                    'client_id': client_id,
                    'orders_quantity': 0
                })
            else:
                self.overall_history = list()
                for order in history['historyOrders']:

                    items_list = list()

                    for order_items in order['items']:
                        items_list.append({
                            'item_sum': order_items['sum'],
                            'item_amount': order_items['amount'],
                            'item_title': order_items['name'],
                        })

                    current_time = iiko.order_info1(order['orderId'], venue.venue_id)['createdTime']

                    orders_history.append({
                        'self': order['isSelfService'],
                        'order_id': order['orderId'],
                        'order_number': order['number'],
                        'order_adress': order['address'],
                        # 'order_organization':order['organizationId'],
                        'order_deliver_date': order['date'],
                        'order_current_date': current_time,
                        'order_phone': order['phone'],
                        'order_discount': order['discount'],
                        'order_total': order['sum'],
                        'order_items': items_list
                    })
            self.overall_history.append({
                'venueId': venue.venue_id,
                'address': venue.address,
                'name': venue.name,
                'local_history': orders_history
            })

        self.render_json({'history': self.overall_history})



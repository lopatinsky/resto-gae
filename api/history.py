import json
import webapp2
from api.base import BaseHandler
import iiko

__author__ = 'Rustemr'


class HistoryRequestHandler(BaseHandler):
    """ /api/history/%s/venue/%s """
    def get(self, client_id,venue_id):
        client_id= client_id[:8] + '-' + client_id[8:12]+'-'+ client_id[12:16]+'-'+client_id[16:20]+'-'+client_id[20:]
        history = iiko.get_history(client_id,venue_id)
        orders_history=list()
        for order in history['historyOrders']:

            items_list=list();

            for order_items in order['items']:

                items_list.append({
                'item_sum':order_items['sum'],
                'item_amount':order_items['amount'],
                'item_title':order_items['name'],
                })

            orders_history.append({
            'self':order['isSelfService'],
            'order_id':order['orderId'],
            'order_number':order['number'],
            'order_adress':order['address'],
            #'order_organization':order['organizationId'],
            'order_deliver_date':order['date'],
            'order_phone':order['phone'],
            'order_discount':order['discount'],
            'order_total':order['sum'],
            'order_items':items_list
             })




        self.render_json({'history': orders_history})



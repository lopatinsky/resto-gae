__author__ = 'dvpermyakov'

from base import BaseHandler
from models.iiko import Venue, ClientInfo, ANDROID_DEVICE, IOS_DEVICE
from models.specials import Notification
from methods.parse_com import send_push, make_general_push_data
import logging


class PushSendingHandler(BaseHandler):
    def get(self):
        venues = Venue.query().fetch()
        self.render('pushes.html', venues=venues)

    def post(self):
        logging.info(self.request.POST)

        text = self.request.get('text')
        head = self.request.get('head')
        venues = Venue.query().fetch()
        chosen_companies = {}
        for venue in venues:
            chosen_companies[venue.company_id] = bool(self.request.get(str(venue.key.id())))

        android_avail = bool(self.request.get('android'))
        ios_avail = bool(self.request.get('ios'))

        def get_client_channel(client_id):
            return 'client_%s' % client_id

        clients = ClientInfo.query().fetch()
        android_channels = []
        ios_channels = []
        for client in clients:
            if not chosen_companies[client.company_id]:
                continue
            device = client.get_device()
            if device == ANDROID_DEVICE and android_avail:
                android_channels.append(get_client_channel(client.key.id()))
            elif device == IOS_DEVICE and ios_avail:
                ios_channels.append(get_client_channel(client.key.id()))
            else:
                customer = client.customer.get() if client.customer else None
                if not customer:
                    continue
                device = customer.get_device()
                if device == ANDROID_DEVICE and android_avail:
                    android_channels.append(get_client_channel(client.key.id()))
                elif device == IOS_DEVICE and ios_avail:
                    ios_channels.append(get_client_channel(client.key.id()))

        result = {}
        if android_avail:
            data = make_general_push_data(text, ANDROID_DEVICE, head)
            response = send_push(android_channels, data, ANDROID_DEVICE)
            #if response.get('result'):
            #    for channel in android_channels:
            #        Notification(client_id=channel.split('_')[1], type=Notification.PUSH_NOTIFICATION)
            result['android'] = {
                'data': data,
                'channels': android_channels,
                'response': response['result'] if response.get('result') else False
            }
        if ios_avail:
            data = make_general_push_data(text, IOS_DEVICE)
            response = send_push(ios_channels, data, IOS_DEVICE)
            #if response.get('result'):
            #    for channel in ios_channels:
            #        Notification(client_id=channel.split('_')[1], type=Notification.PUSH_NOTIFICATION)
            result['ios'] = {
                'data': data,
                'channels': ios_channels,
                'response': response['result'] if response.get('result') else False
            }

        self.render('pushes_result.html', result=result)
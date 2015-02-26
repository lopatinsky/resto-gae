__author__ = 'dvpermyakov'

from models.iiko import ClientInfo, ANDROID_DEVICE, IOS_DEVICE
from models.specials import Notification
from methods.parse_com import send_push, make_general_push_data


def push_venues(chosen_companies, text, head, android_avail, ios_avail):

    def get_client_channel(client_id):
        return 'client_%s' % client_id

    clients = ClientInfo.query().fetch()
    android_channels = []
    ios_channels = []
    for client in clients:
        if client.company_id not in chosen_companies:
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
        if response.get('result'):
            for channel in android_channels:
                Notification(client_id=channel.split('_')[1], type=Notification.PUSH_NOTIFICATION)
        result['android'] = {
            'data': data,
            'channels': android_channels,
            'response': response['result'] if response.get('result') else False
        }
    if ios_avail:
        data = make_general_push_data(text, IOS_DEVICE)
        response = send_push(ios_channels, data, IOS_DEVICE)
        if response.get('result'):
            for channel in ios_channels:
                Notification(client_id=channel.split('_')[1], type=Notification.PUSH_NOTIFICATION)
        result['ios'] = {
            'data': data,
            'channels': ios_channels,
            'response': response['result'] if response.get('result') else False
        }

    return result
# coding=utf-8
from models.iiko.customer import ANDROID_DEVICE
from models.iiko.customer import IOS_DEVICE
from models.iiko.order import Order

__author__ = 'dvpermyakov'

import json

from models.iiko import ClientInfo, CompanyNew
from models.specials import MassPushHistory
from methods.parse_com import send_push, make_mass_push_data
from methods.email.mandrill import send_email


def push_venues(chosen_companies, text, full_text, head, android_avail, ios_avail, user_login, jinja):

    def get_client_channel(client_id):
        return 'client_%s' % client_id

    if chosen_companies:
        clients = ClientInfo.query(ClientInfo.company_id.IN(chosen_companies)).fetch()
    else:
        clients = []
    android_channels = []
    ios_channels = []

    dummy_order = None

    for chosen_company in chosen_companies:
        company = CompanyNew.get_by_id(chosen_company)
        if company.ios_push_channel:
            ios_channels.append(company.ios_push_channel)
        if company.android_push_channel:
            android_channels.append(company.android_push_channel)
        dummy_order = Order(venue_id=company.iiko_org_id)  # for proper parse account

    for client in clients:
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
        data = make_mass_push_data(text, full_text, ANDROID_DEVICE, head)
        response = send_push(android_channels, data, ANDROID_DEVICE, dummy_order)
        result['android'] = {
            'data': data,
            'channels': android_channels,
            'response': response['result'] if response.get('result') else False
        }
    if ios_avail:
        data = make_mass_push_data(text, full_text, IOS_DEVICE, head)
        response = send_push(ios_channels, data, IOS_DEVICE, dummy_order)
        result['ios'] = {
            'data': data,
            'channels': ios_channels,
            'response': response['result'] if response.get('result') else False
        }

    values = {
        'text': text,
        'head': head,
        'android_avail': android_avail,
        'android_channels': android_channels,
        'ios_avail': ios_avail,
        'ios_channels': ios_channels,
        'company_ids': chosen_companies,
        'parse_response': json.dumps(result)
    }

    MassPushHistory(**values).put()
    str_companies = ''.join(['%s, ' % CompanyNew.get_by_id(company_id).app_title for company_id in chosen_companies])
    html_body = jinja.render_template('email/pushes.html', text=text, head=head, str_companies=str_companies, result=result, user=user_login)
    send_email('dvpermyakov1@gmail.com', ['beacon-team@googlegroups.com'], [], u'Рассылкка пушей', html_body)

    return result
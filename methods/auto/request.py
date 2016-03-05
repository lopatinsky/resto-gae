import logging
import urllib
from google.appengine.api import urlfetch

from methods.email.admin import send_error
from models.iiko.company import CompanyNew

__author__ = 'dvpermyakov'


BASE_URL = 'http://doubleb-automation-production.appspot.com/api/admin'


def _request(path, params):
    url = '%s%s' % (BASE_URL, path)
    response = urlfetch.fetch(url, method='POST', payload=urllib.urlencode(params), deadline=10)
    if response.status_code >= 400:
        body = "\n".join((response.status_code, url, str(params), response.content))
        logging.error(body)
        send_error('auto', 'Error in automation request' % response.status_code, body)


def cancel_order(order, auto_token):
    path = '/orders/%s/cancel' % order.key.id()
    params = {
        'token': auto_token
    }
    _request(path, params)


def close_order(order, auto_token):
    path = '/orders/%s/close' % order.key.id()
    params = {
        'token': auto_token
    }
    _request(path, params)


def confirm_order(order, auto_token):
    path = '/orders/%s/confirm' % order.key.id()
    params = {
        'token': auto_token
    }
    _request(path, params)


def update_number_in_auto(order):
    auto_token = CompanyNew.get_by_iiko_id(order.venue_id).auto_token
    path = '/orders/%s/add_number' % order.key.id()
    params = {
        'token': auto_token,
        'number': order.number
    }
    _request(path, params)

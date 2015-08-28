import logging
import urllib
from google.appengine.api import urlfetch

__author__ = 'dvpermyakov'


BASE_URL = 'http://doubleb-automation-production.appspot.com/api/admin'


def cancel_oder(order, auto_venue):
    path = '/orders/%s/cancel' % order.key.id()
    params = {
        'token': auto_venue.token
    }
    url = '%s%s?%s' % (BASE_URL, path, urllib.urlencode(params))
    logging.info(url)
    response = urlfetch.fetch(url, method='POST')
    logging.info(response.status_code)


def close_order(order, auto_venue):
    path = '/orders/%s/close' % order.key.id()
    params = {
        'token': auto_venue.token
    }
    url = '%s%s?%s' % (BASE_URL, path, urllib.urlencode(params))
    logging.info(url)
    response = urlfetch.fetch(url, method='POST')
    logging.info(response.status_code)


def confirm_order(order, auto_venue):
    path = '/orders/%s/confirm' % order.key.id()
    params = {
        'token': auto_venue.token
    }
    url = '%s%s?%s' % (BASE_URL, path, urllib.urlencode(params))
    logging.info(url)
    response = urlfetch.fetch(url, method='POST')
    logging.info(response.status_code)
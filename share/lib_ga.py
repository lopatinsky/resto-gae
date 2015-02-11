import logging
import random
from time import time
import urllib
from google.appengine.api import urlfetch


def _request(req_values, req_headers):
    return urlfetch.fetch('http://www.google-analytics.com/collect', urllib.urlencode(req_values), 'POST', deadline=30)


def gen_ga_cid():
    return '.'.join((str(random.randint(100, 10000000)), str(int(time()))))


def ga_track_page(tracking_id, hostname, page, title, cid=None, v=1, req_headers=None):
    cid_g = cid if cid is not None else gen_ga_cid()
    req_values = {
        'v': v,  # Version.
        'cid': cid_g,  # Anonymous Client ID.
        't': 'pageview',  # Pageview hit type.
        'tid': tracking_id,  # Tracking ID / Property ID.
        'dh': hostname,  # Document hostname.
        'dp': page,  # Page.
        'dt': title,  # Title.
    }
    try:
        _request(req_values, req_headers)
    except Exception as ex:
        logging.exception(ex)
    return cid_g


def ga_track_event(tracking_id, category, action, label=None, value=None, cid=None, v=1, req_headers=None):
    cid_g = cid if cid is not None else gen_ga_cid()
    req_values = {
        'v': v,  # Version.
        'cid': cid_g,  # Anonymous Client ID.
        't': 'event',  # Event hit type
        'tid': tracking_id,  # Tracking ID / Property ID.

        'ec': category,  # Event Category. Required.
        'ea': action,  # Event Action. Required.
    }
    if label:
        req_values['el'] = label
    if value:
        req_values['ev'] = value
    logging.warn(req_values)
    try:
        _request(req_values, req_headers)
    except Exception as ex:
        logging.exception(ex)
    return cid_g

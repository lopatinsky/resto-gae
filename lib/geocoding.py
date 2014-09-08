import json
import logging
import time
import urllib
from google.appengine.api import urlfetch

__author__ = 'quiker'

GEOCODING_KEY = 'AIzaSyCFCmb9MGL22ulEXiHHo6hs3XANIUNrnEI'


def get_address_coordinates(address):
    url = 'https://maps.googleapis.com/maps/api/geocode/json?%s' % urllib.urlencode({
        'sensor': 'false',
        'address': address.encode('utf-8'),
        'key': GEOCODING_KEY
    })
    result = urlfetch.fetch(url, deadline=10)
    result = json.loads(result.content)
    location = result['results'][0]['geometry']['location']
    return location['lat'], location['lng']


def get_timezone_by_coords(lat, lng):
    logging.info("getting timezone for %s, %s", lat, lng)
    url = 'https://maps.googleapis.com/maps/api/timezone/json?%s' % urllib.urlencode({
        'location': '%s,%s' % (lat, lng),
        'timestamp': int(time.time()),
        'key': GEOCODING_KEY
    })
    result = urlfetch.fetch(url, deadline=10)
    result = json.loads(result.content)
    logging.info(result)
    return int(result['rawOffset'] + result['dstOffset'])

import json
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
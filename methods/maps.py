# coding=utf-8

import json
import logging
import time
import urllib
from google.appengine.api import urlfetch

MAPS_API_KEY = 'AIzaSyCFCmb9MGL22ulEXiHHo6hs3XANIUNrnEI'


def get_address_coordinates(address):
    url = 'https://maps.googleapis.com/maps/api/geocode/json?%s' % urllib.urlencode({
        'sensor': 'false',
        'address': address.encode('utf-8'),
        'key': MAPS_API_KEY
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
        'key': MAPS_API_KEY
    })
    result = urlfetch.fetch(url, deadline=10)
    result = json.loads(result.content)
    logging.info(result)
    return int(result['rawOffset'] + result['dstOffset'])


def get_address_by_key(key):
    url = 'https://maps.googleapis.com/maps/api/place/details/json'
    payload = urllib.urlencode({
        'key': MAPS_API_KEY,
        'sensor': 'false',
        'reference': key
    })
    result = urlfetch.fetch(url='%s?%s' % (url, payload), method=urlfetch.GET, deadline=30)
    if result.status_code != 200 or not result.content:
        return None
    try:
        logging.info(result.content)
        obj = json.loads(result.content)
    except:
        return None
    return {
        'address': obj['result']['formatted_address'],
        'location': obj['result']['geometry']['location']
    }


def complete_address_input(address):
    url = 'https://maps.googleapis.com/maps/api/place/autocomplete/json'
    payload = urllib.urlencode({
        'key': MAPS_API_KEY,
        'sensor': 'false',
        'input': address.encode('utf-8'),
        'types': 'geocode',
        'language': 'ru'
    })
    result = urlfetch.fetch(url='%s?%s' % (url, payload), method=urlfetch.GET, deadline=30)
    if result.status_code != 200 or not result.content:
        return []
    try:
        logging.info(result.content)
        obj = json.loads(result.content)
    except:
        return []
    predictions = obj.get('predictions')
    results = []
    for prediction in predictions:
        if 'route' not in prediction.get('types', []):
            continue
        terms = prediction.get('terms', [])
        if len(terms) == 0:
            continue
        results.append({
            'key': prediction.get('reference'),
            'source': 'google',
            'title': terms[0].get('value'),
            'description': ', '.join([t.get('value') for t in terms[1:]]) if len(terms) > 1 else ''
        })
    return results

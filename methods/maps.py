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


def get_cities_by_kladr(number, address):
    url = 'http://kladr-api.ru/api.php'
    payload = urllib.urlencode({
        'token': '548cc93f7c523934798b456f',
        'query': address.encode('utf-8'),
        'contentType': 'city',
        'limit': number
    })
    result = urlfetch.fetch(url='%s?%s' % (url, payload), method=urlfetch.GET, deadline=30)

    if result.status_code != 200 or not result.content:
        return []

    try:
        logging.info(result.content)
        obj = json.loads(result.content)
    except:
        return []

    predictions = obj.get('result')
    cities = []
    for prediction in predictions:
        cities.append({
            'city_id': prediction.get('id')
        })
    return cities


def get_streets_by_kladr(number, city_id, address):
    url = 'http://kladr-api.ru/api.php'
    payload = urllib.urlencode({
        'token': '548cc93f7c523934798b456f',
        'query': address.encode('utf-8'),
        'cityId': city_id,
        'contentType': 'street',
        'withParent': 1,
        'limit': number
    })
    result = urlfetch.fetch(url='%s?%s' % (url, payload), method=urlfetch.GET, deadline=30)

    if result.status_code != 200 or not result.content:
        return []

    try:
        logging.info(result.content)
        obj = json.loads(result.content)
    except:
        return []

    predictions = obj.get('result')
    streets = []
    for prediction in predictions:
        streets.append({
            'city_id': prediction.get('parents')[1].get('id'),
            'city_name': prediction.get('parents')[1].get('name'),
            'street_id': prediction.get('id'),
            'street_name': prediction.get('name'),
            'source': 'kladr'
        })
    return streets


def complete_address_input_by_kladr(address):
    words = address.split(' ')  # address consist of city and street which are separated by ' '.
    cities = get_cities_by_kladr(3, words[0])
    results = []
    for city in cities:
        results.extend(get_streets_by_kladr(3, city['city_id'], words[1]))

    return results
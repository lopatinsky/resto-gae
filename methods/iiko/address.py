import json
from google.appengine.api import memcache
from methods.iiko.base import get_request

__author__ = 'dvpermyakov'


def get_delivery_cities(company):
    city_dicts = memcache.get('iiko_cities_%s' % company.iiko_org_id)
    if not city_dicts:
        response = get_request(company, '/cities/citiesList', {
            'organization': company.iiko_org_id
        })
        city_dicts = [{
            'id': city_dict['id'],
            'name': city_dict['name']
        } for city_dict in json.loads(response)]
        memcache.set('iiko_cities_%s' % company.iiko_org_id, city_dicts, time=3600)
    return city_dicts


def get_delivery_streets(company, city_id):
    street_dicts = memcache.get('iiko_streets_%s' % company.iiko_org_id)
    if not street_dicts:
        response = get_request(company, '/streets/streets', {
            'organization': company.iiko_org_id,
            'city': city_id
        })
        street_dicts = [{
            'id': street_dict['id'],
            'city_id': street_dict['cityId'],
            'name': street_dict['name']
        } for street_dict in json.loads(response)]
        memcache.set('iiko_streets_%s' % company.iiko_org_id, street_dicts, time=3600)
    return street_dicts
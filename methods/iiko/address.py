import bisect
from collections import defaultdict
import json
from methods.iiko.base import get_request
from models.square_table import JsonStorage

__author__ = 'dvpermyakov'


def _process_streets(iiko_street_data):
    result = defaultdict(list)
    for city in iiko_street_data:
        city_name = city['city']['name'].lower()
        streets = [street['name'] for street in city['streets']]
        result[city_name].extend(streets)
    result = {city_name: sorted(streets, key=unicode.lower) for city_name, streets in result.iteritems()}
    return result


def get_cities_and_streets(company, force_update=False):
    storage_key = "streets_%s" % company.iiko_org_id
    result = JsonStorage.get(storage_key)
    if not result or force_update:
        response = get_request(company, '/cities/cities', {
            'organization': company.iiko_org_id
        })
        result = _process_streets(json.loads(response))
        JsonStorage.save(storage_key, result)
    return result


def complete_address_input_by_iiko(company, city, street):
    city = city.lower()
    street_dict = get_cities_and_streets(company)
    if city not in street_dict:
        return []
    city_streets = street_dict[city]
    city_streets_lower = [s.lower() for s in city_streets]
    search = street.lower()

    index = bisect.bisect_left(city_streets_lower, search)
    results = []
    while index < len(city_streets_lower) and city_streets_lower[index].startswith(search):
        street_name = city_streets[index]
        results.append({
            'source': 'iiko',
            'title': street_name,
            'description': street_name,
            'key': street_name
        })
        index += 1
    return results

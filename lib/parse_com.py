import json
import logging
from google.appengine.api import urlfetch

__author__ = 'phil'

parse_accs = [{'master_key': 'YaEHCHCURT6qQFYwvWeTsIwho6cJPSDBhDAz4CS1',
               'client_key': 'CSxzgKDGJwUv7GVySEpkti7nOiHYFJMHR3RYxnU0',
               'rest_api_key': 'vN10st4XD2AD5gF8ziKCgWbo6tyLNE2scmRaXglU',
               'application_id': '8EdzRDGVxjOqnHzv7WU7S6XbhIUBsgzqPk6ax77m'},
              ]

url = 'https://api.parse.com/1/push'

def send_push(channel, alert='', data=None):
    if not data:
        data = {}
    res = ''
    for parse_acc in parse_accs:
        message = {"where": {
            # "deviceType": {"$in": ["ios", "winphone", "js"]},
            "channels": {"$in": [channel]}},
            "data": {"alert": alert}  # , "badge": badge}
        }
        message['data'].update(data)
        payload = json.dumps(message, separators=(',', ':'))
        try:
            result = urlfetch.fetch(url=url,
                                    payload=payload,
                                    method=urlfetch.POST,
                                    headers={"X-Parse-Application-Id": parse_acc['application_id'],
                                             "X-Parse-REST-API-Key": parse_acc['rest_api_key'],
                                             'Content-Type': 'application/json'})
            res += result.content
        except:
            logging.warning('parse.com push send fuckup')
    return res

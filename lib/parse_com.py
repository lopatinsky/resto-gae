import json
import logging
from google.appengine.api import urlfetch

__author__ = 'phil'

parse_accs = [{'master_key': 'P81paIcQLJ9trZCjZu9ITPAGzc1jKXvtVJUP7Z07',
               'client_key': 'dzv4U0BiJZIwCoxfss432UyLZkTLYt0rTdpIQPvf',
               'rest_api_key': '8kKiAG7OBSJTzknzumu6DoXN2NHCIuMTs1RAVdU8',
               'application_id': '6TwyWBKMXJycL3PbOLhi23Jdz8PlM3u2hPVLrhxH'},
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

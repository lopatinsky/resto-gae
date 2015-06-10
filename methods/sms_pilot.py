import json
import logging
from google.appengine.api import urlfetch
from . import email

SMSPILOT_API_KEY = 'YMO7263H170NDGPX2N3863D17EX88HX9P96MFK5O4DKKBQ8D9J897J9O6TQH8741'


def send_sms(from_, to, text):
    data = {
        'apikey': SMSPILOT_API_KEY,
        'send': [
            {
                'from': from_,
                'to': phone,
                'text': text
            } for phone in to
        ]
    }
    response = urlfetch.fetch("http://smspilot.ru/api2.php", payload=json.dumps(data), method='POST',
                              headers={'Content-Type': 'application/json'}).content
    logging.info(response)
    result = json.loads(response)

    success = "send" in result
    for message in result.get("send", []):
        if message["status"] != "0":
            success = False
    if not success:
        email.send_error("sms", "SMS failure", response)
    return success, json.loads(response)

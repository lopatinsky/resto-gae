# coding=utf-8
import logging

from google.appengine.api import urlfetch
import json

MANDRILL_SEND_EMAIL_URL = 'https://mandrillapp.com/api/1.0/messages/send.json'
API_KEY = 'vcJnxtopNKq4gKaliwhDPg'


def send_email(from_email, to_emails, cc_emails, subject, body):
    payload = {
        'key': API_KEY,
        'message': {
            'html': body,
            'subject': subject,
            'from_email': from_email,
            'to': [{'email': to_email} for to_email in to_emails] +
                  [{'email': cc_email, "type": "cc"} for cc_email in cc_emails]
        }
    }
    payload = json.dumps(payload)
    result = urlfetch.fetch(MANDRILL_SEND_EMAIL_URL, payload=payload, method=urlfetch.POST,
                            headers={'Content-Type': 'application/json'}, deadline=10)
    logging.info("%s %s", result.status_code, result.content)
    return json.loads(result.content)

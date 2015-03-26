__author__ = 'dvpermyakov'

ACCOUNT_SID = 'AC5d5afb5b56277b1a8b281beb198020e8'
AUTH_TOKEN = 'ae8a9880257d3adf64fb9fe3d0967981'
FROM_NUMBER = '+14804481171'

from libs.twilio import rest
import logging


def send_sms(receiver_phones, text):
    client = rest.TwilioRestClient(ACCOUNT_SID, AUTH_TOKEN)
    for phone in receiver_phones:
        if len(phone) == 11 and phone.startswith('79'):
            phone = '+%s' % phone
        elif len(phone) == 11 and phone.startswith('8'):
            phone = '+7%s' % phone[1:]
        elif len(phone) == 10:
            phone = '+7%s' % phone
        values = {
            'body': text,
            'from_': FROM_NUMBER,
            'to': phone
        }
        client.messages.create(**values)
        logging.info(phone)
    logging.info('list: %s' % client.messages.list)
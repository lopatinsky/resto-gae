#coding:utf-8
from google.appengine.api import urlfetch
import json
from config import config
import logging
from models.iiko import Venue

APP_KEY = {
    Venue.EMPATIKA: '112172995912421866',
    Venue.COFFEE_CITY: '112172995912421866'
}
BASE_URL = 'https://api.branch.io'

ANDROID_URL = {
    Venue.EMPATIKA: "http://coffeeandthecity.ru/",
    Venue.COFFEE_CITY: "http://coffeeandthecity.ru/"
}
IOS_URL = {
    Venue.EMPATIKA: "http://coffeeandthecity.ru/",
    Venue.COFFEE_CITY: "http://coffeeandthecity.ru/"
}
DESKTOP_URL = {
    Venue.EMPATIKA: "http://coffeeandthecity.ru/",
    Venue.COFFEE_CITY: "http://coffeeandthecity.ru/"
}

VK = 0
FACEBOOK = 1
SMS = 2
EMAIL = 3
WHATS_APP = 4
SKYPE = 5
TWITTER = 6
INSTAGRAM = 7
OTHER = 8

CHANNELS = [VK, FACEBOOK, SMS, EMAIL, WHATS_APP, SKYPE, TWITTER, INSTAGRAM, OTHER]

CHANNEL_MAP = {
    VK: 'vk',
    FACEBOOK: 'facebook',
    SMS: 'sms',
    EMAIL: 'email',
    WHATS_APP: 'whats app',
    SKYPE: 'skype',
    TWITTER: 'twitter',
    INSTAGRAM: 'instagram',
    OTHER: 'other'
}

SHARE = 0
INVITATION = 1
GIFT = 2

FEATURE_MAP = {
    SHARE: u'Расскажи друзьям',
    INVITATION: u'Пригласи друга',
    GIFT: u'Подари кружку другу'
}


def create_url(venue_id, share_id, feature, channel, user_agent, custom_tags=None, recipient=None, alias=None):
    params = {
        'app_id': APP_KEY[venue_id],
        'data': {
            'phone': recipient.get('phone') if recipient else None,
            'name': recipient.get('name') if recipient else None,
            'share_id': share_id,
            '$desktop_url': DESKTOP_URL[venue_id],
            '$android_url': ANDROID_URL[venue_id],
            '$ios_url': IOS_URL[venue_id],
            '$deeplink_path': '',
            '$always_deeplink': False
        },
        'alias': alias if alias else None,
        'identity': share_id,
        'tags': [config.BRANCH_IO_TAG, user_agent],
        'campaign': u'(запуск 02.04.2015)',
        'feature': FEATURE_MAP[feature],
        'channel': CHANNEL_MAP[channel]
    }
    if custom_tags:
        for item in custom_tags.items():
            params['tags'].append("%s__%s" % item)
    url = '%s%s' % (BASE_URL, '/v1/url')
    response = urlfetch.fetch(url=url, payload=json.dumps(params), method=urlfetch.POST,
                              headers={'Content-Type': 'application/json'}, deadline=10)
    logging.info(response.status_code)
    logging.info(response.content)
    response = response.content
    return json.loads(response)['url']

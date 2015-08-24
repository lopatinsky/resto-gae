import json
import logging
import urllib
from google.appengine.api import urlfetch, memcache
from models.iiko import IikoApiLogin, PlatiusLogin

__author__ = 'dvpermyakov'

PLATIUS_BASE_URL = 'https://iiko.net:9900/api/0'
IIKO_BIZ_BASE_URL = 'https://iiko.biz:9900/api/0'

CAT_GIFTS_GROUP_ID = 'fca63e6b-b622-4d99-9453-b8c3372c6179'


def __get_iiko_base_url(iiko_biz):
    return IIKO_BIZ_BASE_URL if iiko_biz else PLATIUS_BASE_URL


def get_request(company, api_path, params, force_platius=False):
    def do():
        url = '%s%s' % (iiko_base_url, api_path)
        if params:
            url = '%s?%s' % (url, urllib.urlencode(params))
        logging.info(url)
        return urlfetch.fetch(url, deadline=30, validate_certificate=False)

    iiko_biz = company.new_endpoints and not force_platius
    iiko_base_url = __get_iiko_base_url(iiko_biz)
    params['access_token'] = get_access_token(company, iiko_biz=iiko_biz)
    result = do()
    if result.status_code == 401:
        logging.warning("bad token")
        params['access_token'] = get_access_token(company, iiko_biz=iiko_biz, refresh=True)
        result = do()
    return result.content


def post_request(company, api_path, params, payload, force_platius=False):
    def do():
        url = '%s%s' % (iiko_base_url, api_path)
        if params:
            url = '%s?%s' % (url, urllib.urlencode(params))
        json_payload = json.dumps(payload)
        logging.info("PAYLOAD %s" % str(json_payload))
        logging.info(url)

        return urlfetch.fetch(url, method='POST', headers={'Content-Type': 'application/json'}, payload=json_payload,
                              deadline=30, validate_certificate=False)

    iiko_biz = company.new_endpoints and not force_platius
    iiko_base_url = __get_iiko_base_url(iiko_biz)
    params['access_token'] = get_access_token(company, iiko_biz=iiko_biz)
    result = do()
    if result.status_code == 401:
        logging.warning("bad token")
        params['access_token'] = get_access_token(company, iiko_biz=iiko_biz, refresh=True)
        result = do()
    return result.content


def get_access_token(company, iiko_biz, refresh=False):
    memcache_key_format = 'iiko_biz_token_%s' if iiko_biz else 'platius_token_%s'
    memcache_key = memcache_key_format % company.iiko_login
    token = memcache.get(memcache_key)
    if not token or refresh:
        token = _fetch_access_token(company, iiko_biz)
        memcache.set(memcache_key, token, time=10*60)
    return token


def _fetch_access_token(company, iiko_biz):
    login_entity = IikoApiLogin.get_by_id(company.iiko_login) if iiko_biz \
        else PlatiusLogin.get_by_id(company.platius_login)
    data = urllib.urlencode({
        "user_id": login_entity.login,
        "user_secret": login_entity.password
    })
    result = urlfetch.fetch(
        __get_iiko_base_url(iiko_biz) + '/auth/access_token?%s' % data, deadline=10, validate_certificate=False)
    return result.content.strip('"')

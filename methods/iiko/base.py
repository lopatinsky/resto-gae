import json
import logging
import urllib
from google.appengine.api import urlfetch, memcache

from methods.json_encoder import BetterFloatJsonEncoder
from models.iiko import IikoApiLogin, PlatiusLogin
from models.iiko.company import CompanyNew

__author__ = 'dvpermyakov'

PLATIUS_BASE_URL = 'https://platius.ru:9900/api/0'
IIKO_BIZ_BASE_URL = 'https://iiko.biz:9900/api/0'

CAT_GIFTS_GROUP_ID = 'fca63e6b-b622-4d99-9453-b8c3372c6179'


def __get_iiko_base_url(iiko_biz):
    return IIKO_BIZ_BASE_URL if iiko_biz else PLATIUS_BASE_URL


def _should_use_iiko_biz(company, force_platius):
    """Determines if the API request should use iiko.biz or platius.
    If the company is not using iiko.biz (company.new_endpoints is False), always use platius.
    If the company does not have platius org id, always use iiko.biz.
    Otherwise (if we can use both), check the force_platius parameter.
    """
    if not company.new_endpoints:
        return False  # can not use iiko_biz if company uses platius
    if not company.platius_org_id:
        return True  # can not use platius if no platius org id
    return not force_platius


def _replace_org_id(api_path, company, params, payload, iiko_biz):
    if not iiko_biz:
        if params.get('organization'):
            params['organization'] = company.platius_org_id
        if payload and payload.get('organization'):
            payload['organization'] = payload['restaurantId'] = company.platius_org_id
        api_path = api_path.replace(company.iiko_org_id, company.platius_org_id)
    return api_path


def _restore_org_id(company, payload):
    if payload.get('organization'):
        payload['organization'] = payload['restaurantId'] = company.iiko_org_id


def get_request(company, api_path, params, force_platius=False, deadline=30):
    def do():
        url = '%s%s' % (iiko_base_url, api_path)
        if params:
            url = '%s?%s' % (url, urllib.urlencode(params))
        logging.info(url)
        return urlfetch.fetch(url, deadline=deadline, validate_certificate=False)

    iiko_biz = _should_use_iiko_biz(company, force_platius)
    iiko_base_url = __get_iiko_base_url(iiko_biz)
    api_path = _replace_org_id(api_path, company, params, None, iiko_biz)

    params['access_token'] = get_access_token(company, iiko_biz=iiko_biz)
    result = do()
    if result.status_code == 401:
        logging.warning("bad token")
        params['access_token'] = get_access_token(company, iiko_biz=iiko_biz, refresh=True)
        result = do()
    return result.content


def post_request(company, api_path, params, payload, force_platius=False, deadline=30):
    def do():
        url = '%s%s' % (iiko_base_url, api_path)
        if params:
            url = '%s?%s' % (url, urllib.urlencode(params))
        json_payload = json.dumps(payload, cls=BetterFloatJsonEncoder)
        logging.info("PAYLOAD %s" % str(json_payload))
        logging.info(url)

        return urlfetch.fetch(url, method='POST', headers={'Content-Type': 'application/json'}, payload=json_payload,
                              deadline=deadline, validate_certificate=False)

    iiko_biz = _should_use_iiko_biz(company, force_platius)
    iiko_base_url = __get_iiko_base_url(iiko_biz)
    api_path = _replace_org_id(api_path, company, params, payload, iiko_biz)

    params['access_token'] = get_access_token(company, iiko_biz=iiko_biz)
    result = do()
    if result.status_code == 401:
        logging.warning("bad token")
        params['access_token'] = get_access_token(company, iiko_biz=iiko_biz, refresh=True)
        result = do()

    _restore_org_id(company, payload)
    return result.content


def get_access_token(company, iiko_biz, refresh=False):
    if iiko_biz:
        memcache_key = 'iiko_biz_token_%s' % company.iiko_login
    else:
        memcache_key = 'platius_token_%s' % company.platius_login
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

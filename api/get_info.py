# coding=utf-8

from api.base import BaseHandler
from methods.maps import get_address_by_key


class GetAddressByKeyHandler(BaseHandler):

    """ /api/get_info """

    def get(self):
        key = self.request.get('key')

        info = get_address_by_key(key)

        return self.render_json(info)

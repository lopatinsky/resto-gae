import json
from handlers.api.base import BaseHandler
from methods.maps import get_address_by_key

__author__ = 'dvpermyakov'


class GetAddressByKeyHandler(BaseHandler):
    def get(self):
        key = self.request.get('key')
        info = get_address_by_key(key)
        return json.loads(self.render_json(info)).get()
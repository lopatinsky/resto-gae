import json
import logging
from webapp2 import RequestHandler


class ExtBaseHandler(RequestHandler):
    def check_auth(self):
        return True

    def render_json(self, obj):
        self.response.headers["Content-Type"] = "application/json"
        self.response.write(json.dumps(obj, separators=(',', ':')))

    def dispatch(self):
        if not self.check_auth():
            self.abort(401)
        return super(ExtBaseHandler, self).dispatch()


class GAEAuthBaseHandler(ExtBaseHandler):
    ALLOWED_IDS = ()

    def check_auth(self):
        header = self.request.headers.get("X-Appengine-Inbound-AppId")
        logging.debug("header app_id is %s, allowed app_ids are %s", header, self.ALLOWED_IDS)
        return header in self.ALLOWED_IDS

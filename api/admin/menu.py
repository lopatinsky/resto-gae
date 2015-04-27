from models.admin import Admin
from models.iiko import DeliveryTerminal

__author__ = 'dvpermyakov'

from ..base import BaseHandler


class MenuHandler(BaseHandler):
    def get(self):
        token = self.request.get("token")
        admin = Admin.query(Admin.token == token).get()
        if not admin:
            self.abort(401)
        self.redirect('/api/venue/%s/menu?all' % admin.delivery_terminal_id)


class DynamicInfoHandler(BaseHandler):
    def get(self):
        token = self.request.get("token")
        admin = Admin.query(Admin.token == token).get()
        if not admin:
            self.abort(401)
        self.render_json({
            'dynamic': DeliveryTerminal.get_by_id(admin.delivery_terminal_id).dynamic_dict()
        })
# coding:utf-8

__author__ = 'dvpermyakov'

from ..base import BaseHandler
from models.admin import Admin
import json
import logging


class LoginHandler(BaseHandler):
    def post(self):
        logging.info(self.request.POST)
        token = self.request.get('token')
        info = json.loads(self.request.get('info'))
        values = {
            'token': token,
            'company_id': info['company_id'],
            'custom': info['custom'],
        }
        admin = Admin(**values)
        admin.put()

        self.render_json({
            'status': 'success'
        })


class LogoutHandler(BaseHandler):

    def send_error(self, description):
        self.response.set_status(400)
        self.render_json({
            "description": description
        })

    def post(self):
        logging.info(self.request.POST)
        token = self.request.get('token')
        admin = Admin.query(Admin.token == token).get()
        if not admin:
            self.send_error(u'Токен не существует')
        else:
            admin.key.delete()
            self.render_json({
                'status': 'success'
            })
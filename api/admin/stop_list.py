# coding=utf-8
import json
from models.admin import Admin
from ..base import BaseHandler
from methods import iiko_api
from models.iiko import DeliveryTerminal


__author__ = 'dvpermyakov'


class ItemStopListHandler(BaseHandler):
    def send_error(self, description):
        self.response.set_status(400)
        self.render_json({
            'success': False,
            'description': description
        })

    def post(self):
        token = self.request.get("token")
        admin = Admin.query(Admin.token == token).get()
        if not admin:
            self.abort(401)
        delivery_terminal = DeliveryTerminal.get_by_id(admin.delivery_terminal_id)
        if not delivery_terminal:
            self.send_error(u'Вы не привязаны к точке')
        stop_list = json.loads(self.request.get('stop_list'))
        for item_id in stop_list.get('stopped'):
            item = iiko_api.get_product_from_menu(admin.company_id, product_id=item_id)
            if not item:
                return self.send_error(u'Продукт не найден')
            if item_id in delivery_terminal.item_stop_list:
                return self.send_error(u'Продукт %s уже в стоп-листе' % item.get('name', ''))
            delivery_terminal.item_stop_list.append(item_id)
        for item_id in stop_list.get('recovered'):
            item = iiko_api.get_product_from_menu(admin.company_id, product_id=item_id)
            if not item:
                return self.send_error(u'Продукт не найден')
            if item_id not in delivery_terminal.item_stop_list:
                return self.send_error(u'Продукт %s еще не в стоп-листе' % item.get('name', '')

                )
            delivery_terminal.item_stop_list.remove(item_id)
        delivery_terminal.put()
        self.render_json({
            'success': True
        })
# coding=utf-8

from methods import iiko_api
from models.admin import Admin
from models.iiko import DeliveryTerminal

__author__ = 'dvpermyakov'

from ..base import BaseHandler


def _process_category(category):
    return {
        "info": {
            "category_id": category["id"],
            "title": category["name"]
        },
        "items": [_convert_product(p) for p in category["products"]],
        "children": [_process_category(c) for c in category["children"]]
    }


def _convert_product(product):
    return {
        "id": product["productId"],
        "title": product["name"]
    }


class MenuHandler(BaseHandler):
    def get(self):
        token = self.request.get("token")
        admin = Admin.query(Admin.token == token).get()
        if not admin:
            self.abort(401)
        menu = iiko_api.get_menu(admin.company_id)
        processed_menu = [_process_category(c) for c in menu]
        self.render_json({
            "menu": processed_menu
        })


class DynamicInfoHandler(BaseHandler):
    def get(self):
        token = self.request.get("token")
        admin = Admin.query(Admin.token == token).get()
        if not admin:
            self.abort(401)
        self.render_json({
            'dynamic': DeliveryTerminal.get_by_id(admin.delivery_terminal_id).dynamic_dict()
        })
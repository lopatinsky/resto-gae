# coding=utf-8
from handlers.api.base import BaseHandler
from methods.iiko.customer import get_customer_by_card
from models.iiko import ClientInfo, CompanyNew, BonusCardHack

__author__ = 'dvpermyakov'


class SaveClientInfoHandler(BaseHandler):
    def post(self, company_id):
        email = self.request.get("client_email")
        phone = self.request.get("client_phone")
        user_agent = self.request.headers['User-Agent']
        key = ClientInfo(company_id=int(company_id), email=email, phone=phone, user_agent=user_agent).put()
        self.render_json({'id': key.id()})


class SaveBonusCardHandler(BaseHandler):
    def get(self, company_id):
        card = self.request.get("card")
        iiko_customer = get_customer_by_card(CompanyNew.get_by_id(int(company_id)), card)
        if 'httpStatusCode' in iiko_customer:
            self.response.set_status(400)
            return self.render_json({'description': u'Не удалось найти бонусную карту'})

        BonusCardHack(id=iiko_customer['phone'], customer_id=iiko_customer['id']).put()
        self.render_json({'phone': '+' + iiko_customer['phone']})
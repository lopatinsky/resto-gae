# coding=utf-8
import logging
from ..base import BaseHandler
from models.specials import MivakoGift


class MivakoPromoInfoHandler(BaseHandler):
    def get(self):
        promo_info = {
            "title": u"Подари ролл другу!",
            "text": u"Укажи номер телефона друга и мы подарим ему ролл \"Калифорния с лососем\" при первом заказе.",
            "image": "http://lh3.googleusercontent.com/"
                     "2rfgbXcm1-viN8uYegsD-SYgW7KVBqV5v_RH8o5FGIZCINtdtfxMjoEt9Xxw5VlDIxrrmSJjpm0QjyWlO8oN9tAP8Rk=s600"
        }
        self.render_json(promo_info)


class MivakoPromoSendGiftHandler(BaseHandler):
    def post(self):
        from_ = self.request.get("from")
        to = self.request.get("to").split(",")
        names = self.request.get("names").split(",")
        if not to or len(to) != len(names):
            self.abort(400)

        recipients = zip(to, names)
        for phone, name in recipients:
            MivakoGift(sender=from_, recipient=phone, recipient_name=name,
                       gift_item=u"ролл \"Калифорния с лососем\"").put()

        logging.info("from: %s", from_)
        logging.info("to: %r", recipients)

        self.render_json({
            "sms": u"""Привет! Дарю тебе ролл "Калифорния с лососем"!
Получи его при заказе в ресторане www.mivako.ru
Скачай приложение: https://clck.ru/9NFUj"""
        })


def get_mivako_iiko_promos():
    return [
        {
            "name": u"Первый заказ",
            "description": u"Скидка 10% на первый заказ",
            "start": None,
            "end": None,
            "image_url": None,
            "id": "0",
            "display_type": 1,
        },
        {
            "name": u"Бонусная программа",
            "description": u"При каждом заказе Вы получаете от 3% до 10% от суммы заказа на свой бонусный счет.",
            "start": None,
            "end": None,
            "image_url": None,
            "id": "1",
            "display_type": 1,
        },
        {
            "name": u"День рождения",
            "description": u"Если Вы именинник, то для вас мы сделаем скидку 15% на весь заказ. "
                           u"Сообщите о своем дне рождении оператору и приготовьте паспорт — "
                           u"его необходимо показать курьеру при доставке.",
            "start": None,
            "end": None,
            "image_url": None,
            "id": "3",
            "display_type": 1,
        }
    ]

# coding=utf-8
import logging
from ..base import BaseHandler
from models.specials import MivakoGift


class MivakoPromoInfoHandler(BaseHandler):
    def get(self):
        self.render_json({
            "title": u"Подари ролл другу!",
            "text": u"Укажи номер телефона друга и мы подарим ему ролл \"Филадельфия Люкс\" при первом заказе через мобильное приложение.",
            "image": "http://lh6.ggpht.com/8zevGQVTtrVFeEE2CNfHX3fXjV4BiPCd_EtlIdAs0Zq_OZ0sU9wrz9w2TOsbWUkVChtviitwCdFfk5PObmLW0WXqc9A"
        })


class MivakoPromoSendGiftHandler(BaseHandler):
    def post(self):
        from_ = self.request.get("from")
        to = self.request.get("to").split(",")
        names = self.request.get("names").split(",")
        if not from_ or not to or len(to) != len(names):
            self.abort(400)

        recipients = zip(to, names)
        for phone, name in recipients:
            MivakoGift(sender=from_, recipient=phone, recipient_name=name,
                       gift_item=u"ролл \"Филадельфия Люкс\"").put()

        logging.info("from: %s", from_)
        logging.info("to: %r", recipients)

        self.render_json({
            "sms": u"""Привет! Дарю тебе ролл "Филадельфия Люкс"!
Получи его при заказе в ресторане www.mivako.ru
Скачай приложение: https://clck.ru/9NFUj"""
        })

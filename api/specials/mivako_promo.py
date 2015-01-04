# coding=utf-8
import logging
from ..base import BaseHandler
from models.specials import MivakoGift


MIVAKO_NY2015_ENABLED = True


class MivakoPromoInfoHandler(BaseHandler):
    def get(self):
        promo_info = {
            "title": u"Подари ролл другу!",
            "text": u"Укажи номер телефона друга и мы подарим ему ролл \"Филадельфия Люкс\" при первом заказе.",
            "image": "http://lh6.ggpht.com/"
                     "8zevGQVTtrVFeEE2CNfHX3fXjV4BiPCd_EtlIdAs0Zq_OZ0sU9wrz9w2TOsbWUkVChtviitwCdFfk5PObmLW0WXqc9A"
        }
        if MIVAKO_NY2015_ENABLED:
            promo_info["ny2015"] = {
                "title": u"Новогодняя акция!",
                "text": u"С 3 по 13 января оплати заказ<br>"
                        u"картой <b>MasterCard</b> через приложение<br>"
                        u"и получи ролл Дракон в подарок!",
                "image": "http://lh5.ggpht.com/"
                         "SQjmpZKTSMKo9KZisAt_Uetj5bVWaxbV9YqKh67ScXmovZXPVIS_ZM-j1Ug7-HoOsFm_YQ31DSiXn94R6N6W-xVVK0M"
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
                       gift_item=u"ролл \"Филадельфия Люкс\"").put()

        logging.info("from: %s", from_)
        logging.info("to: %r", recipients)

        self.render_json({
            "sms": u"""Привет! Дарю тебе ролл "Филадельфия Люкс"!
Получи его при заказе в ресторане www.mivako.ru
Скачай приложение: https://clck.ru/9NFUj"""
        })

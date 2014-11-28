# coding=utf-8
from google.appengine.api import mail
from ..base import BaseHandler
from models.specials import MivakoGift


class MivakoPromoInfoHandler(BaseHandler):
    def get(self):
        self.render_json({
            "title": u"Подари ролл другу!",
            "text": u"Укажи номер телефона друга и мы подарим ему Ролл Калифорния при первом заказе через мобильное приложение.",
            "image": "http://lh5.ggpht.com/Fk4kCTuAWgk3d4_Lz48eW_Ca-gHLIPc2Z5kNuubihU_1mCegklUXiy6ANGrqmeRmpB75EMbMXaO5EwaYzC_mJ4azRF8"
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
            MivakoGift(sender=from_, recipient=phone, recipient_name=name).put()

        recipients_str = "\n\n".join([u"Имя: %s\nТелефон: %s" % (name, phone)
                                      for phone, name in recipients])

        mail_body = u"""Отправитель: %s

Получатели:

%s
""" % (from_, recipients_str)

        # TODO send to Mivako
        # mail.send_mail("mivako_gifts@empatika-resto.appspotmail.com", SOME_EMAIL, u"Подарок в Мивако", mail_body)
        # send to ourselves
        mail.send_mail_to_admins("mivako_gifts@empatika-resto.appspotmail.com", u"Подарок в Мивако", mail_body)

        self.render_json({
            "sms": u"""Привет! Дарю тебе ролл "Филадельфия"!
Получи его при заказе в ресторане www.mivako.ru
Скачай приложение: http://tiny.cc/_______"""
        })

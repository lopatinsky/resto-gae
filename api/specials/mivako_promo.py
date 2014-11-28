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
        if not from_ or not to:
            self.abort(400)

        for recipient in to:
            MivakoGift(sender=from_, recipient=recipient).put()
        mail_body = u"""Отправитель: %s
Получатели:
%s
""" % (from_, "\n".join(to))
        # TODO send to Mivako
        # mail.send_mail("mivako_gifts@empatika-resto.appspotmail.com", SOME_EMAIL, u"Подарок в Мивако", mail_body)
        # TODO send to ourselves
        # mail.send_mail_to_admins("mivako_gifts@empatika-resto.appspotmail.com", u"Подарок в Мивако", mail_body)
        mail.send_mail("mivako_gifts@empatika-resto.appspotmail.com", "mdburshteyn@gmail.com",
                       u"Подарок в Мивако", mail_body)
        self.render_json({})

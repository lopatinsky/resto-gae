# coding=utf-8
import logging
from google.appengine.api import mail
import webapp2
from models.specials import MivakoGift


_MAIL_SENDER = "mivako_gifts@empatika-resto.appspotmail.com"
_MAIL_RECIPIENTS = ["mnemtsan@gmail.com", "delivery@mivako.ru"]
_MAIL_SUBJECT = u"Подарки в Мивако"


class MivakoGiftsEmailHandler(webapp2.RequestHandler):
    def get(self):
        gifts = MivakoGift.query(MivakoGift.emailed == False).fetch()
        if not gifts:
            return

        template = u"Отправитель: %s\nИмя получателя: %s\nТелефон получателя: %s\nПодарок: %s"
        messages = []
        for g in gifts:
            messages.append(template % (g.sender, g.recipient_name, g.recipient, g.gift_item))

        mail_body = "\n\n".join(messages)
        logging.info(mail_body)
        mail.send_mail_to_admins(_MAIL_SENDER, _MAIL_SUBJECT, mail_body)
        try:
            mail.send_mail(_MAIL_SENDER, _MAIL_RECIPIENTS, _MAIL_SUBJECT, mail_body)
        except Exception as e:
            logging.exception(e)
            mail.send_mail_to_admins(_MAIL_SENDER, u"Ошибка отправки подарков в Мивако", e.message)
        else:
            for g in gifts:
                g.emailed = True
                g.put()

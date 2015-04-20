# coding=utf-8

from google.appengine.api import mail
from webapp2 import RequestHandler
from methods import filter_phone


class IikoBizAppHandler(RequestHandler):
    def get(self):
        self.response.content_type = "text/plain"
        self.response.write("""Hello world!
This is a stub for iiko.biz integration page.
Request params is %s""" % (self.request.params,))


class IikoBizSubmitHandler(RequestHandler):
    def post(self):
        self.response.content_type = "text/plain;charset=utf-8"
        email = self.request.get('email')
        phone = filter_phone(self.request.get('phone'))[1:]
        if len(phone) != 11:
            self.response.write(u"Неверный номер телефона, попробуйте еще раз")
            return
        phone = "+%s (%s) %s-%s-%s" % (phone[0], phone[1:4], phone[4:7], phone[7:9], phone[9:])
        mail_body = u"Телефон: %s, email: %s" % (phone, email)
        mail.send_mail("landing@empatika-resto.appspotmail.com", "mdburshteyn@gmail.com",
                       "Новая заявка с landing", mail_body)
        self.response.write(u"Спасибо! Мы свяжемся с Вами в течение дня.")

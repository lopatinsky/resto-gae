# coding=utf-8

from google.appengine.api import mail
from webapp2 import RequestHandler
from methods.rendering import filter_phone
from methods.web_i18n import make_getter, lang_selector


class IikoBizAppHandler(RequestHandler):
    def get(self):
        return self.redirect("http://rbcn.mobi/")
        self.response.content_type = "text/plain"
        self.response.write("""Hello world!
This is a stub for iiko.biz integration page.
Request params is %s""" % (self.request.params,))


class IikoBizSubmitHandler(RequestHandler):
    def post(self):
        t = make_getter(lang_selector(self.request))

        self.response.content_type = "text/plain;charset=utf-8"
        email = self.request.get('email')
        phone = filter_phone(self.request.get('phone'))
        if not phone:
            self.response.write(t["RESULT_WRONG_PHONE"])
            return
        phone = phone[1:]
        phone = "+%s (%s) %s-%s-%s" % (phone[0], phone[1:4], phone[4:7], phone[7:9], phone[9:])
        mail_body = u"Телефон: %s, email: %s" % (phone, email)
        mail.send_mail_to_admins("landing@empatika-resto.appspotmail.com", "Новая заявка с landing", mail_body)
        self.response.write(t["RESULT_OK"])

# coding=utf-8

from datetime import timedelta

from google.appengine.api import app_identity, mail
from webapp2_extras import jinja2

from config import config
from methods.email import mandrill
from models.iiko import CompanyNew

_EMAIL_DOMAIN = "%s.appspotmail.com" % app_identity.get_application_id()
_DEFAULT_EMAIL = "mdburshteyn@gmail.com"


def send_error(scope, subject, body, html=None):
    subject = "[Resto] " + subject
    if config.DEBUG:
        subject = "[Test]" + subject
    sender = "%s_errors@%s" % (scope, _EMAIL_DOMAIN)
    recipients = config.ERROR_EMAILS.get(scope, _DEFAULT_EMAIL)
    kw = {'html': html} if html else {}
    if recipients == "admins":
        mail.send_mail_to_admins(sender, subject, body, **kw)
    else:
        try:
            mail.send_mail(sender, recipients, subject, body, **kw)
        except:
            pass


_EXPRESS_CITY_MAPPING = {
    u"Егорьевск": "orangekspress@mail.ru",
    u"Одинцово": "o_express@mail.ru",
    u"Домодедово": "orange.exspress@mail.ru",
    u"Подольск": "orengeexpress-podolsk@mail.ru",
    u"Климовск": "orengeexpress-podolsk@mail.ru",
    u"Авиагородок": "aviogorodok777@mail.ru",
}


def get_order_email_address(order):
    if order.venue_id == CompanyNew.ORANGE_EXPRESS:
        return _EXPRESS_CITY_MAPPING.get(order.address['city'])
    elif order.venue_id == CompanyNew.MIVAKO:
        return "delivery@mivako.ru"
    elif order.venue_id == CompanyNew.SUSHI_TIME:
        return "stdostavka@mail.ru"
    elif order.venue_id == CompanyNew.OMNOMNOM:
        return "univerfoods@mail.ru"
    elif order.venue_id == CompanyNew.BURGER_CLUB:
        return "astra-burgerclub@mail.ru"
    elif order.venue_id == CompanyNew.GIOTTO:
        return "zakaz@giottoclub.ru"
    return None


def send_order_email(order, customer, company):
    address = get_order_email_address(order)
    if not address:
        return None

    time = (order.date + timedelta(seconds=company.get_timezone_offset())).strftime("%d.%m.%Y %H:%M")
    body = jinja2.get_jinja2().render_template("/email/express-order.html",
                                               order=order, customer=customer, time=time)
    return mandrill.send_email(
        "noreply-order@ru-beacon.ru",
        [address],
        [],
        u"Новый заказ",
        body)

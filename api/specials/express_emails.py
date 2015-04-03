# coding=utf-8
from datetime import timedelta
from methods import mandrill
from webapp2_extras import jinja2

_CITY_MAPPING = {
    u"Егорьевск": "orangekspress@mail.ru",
    u"Одинцово": "o_express@mail.ru",
    u"Домодедово": "orange.exspress@mail.ru",
    u"Подольск": "orengeexpress-podolsk@mail.ru",
    u"Климовск": "orengeexpress-podolsk@mail.ru",
}


def send_express_email(order, customer, company):
    time = (order.date + timedelta(seconds=company.get_timezone_offset())).strftime("%d.%m.%Y %H:%M")
    body = jinja2.get_jinja2().render_template("/email/express-order.html",
                                               order=order, customer=customer, time=time)
    return mandrill.send_email(
        "noreply-order@ru-beacon.ru",
        [_CITY_MAPPING.get(order.address['city'])],
        ["beacon-team@googlegroups.com"],
        u"Новый заказ",
        body)

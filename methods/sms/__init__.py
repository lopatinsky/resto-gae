# coding=utf-8
from . import sms_pilot
from models.iiko.company import CompanyNew

__author__ = 'dvpermyakov'

_CONFIRMATION_TEXT = u"Ваш заказ №%s готовится, ожидайте доставку. %s"


def send_confirmation(order_key):
    order = order_key.get()
    company = CompanyNew.get_by_iiko_id(order.venue_id)
    phone = order.customer.get().phone
    sms_text = _CONFIRMATION_TEXT % (order.number, company.app_title)

    success, _ = sms_pilot.send_sms("INFORM", [phone[1:]], sms_text)

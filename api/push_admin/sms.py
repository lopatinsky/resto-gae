# coding=utf-8
import time

from .base import BaseHandler
from methods import sms_pilot, filter_phone
from methods.auth import push_admin_user_required
from models.iiko import Order
from models.specials import OrderSmsHistory


_CONFIRMATION_TEXT = u"Ваш заказ №%s готовится, ожидайте доставку. Оранжевый Экспресс"


class SmsAdminHandler(BaseHandler):
    @push_admin_user_required
    def get(self):
        company = self.user.company.get()
        orders = Order.query(Order.status.IN((Order.APPROVED, Order.NOT_APPROVED, Order.UNKNOWN)),
                             Order.venue_id == company.iiko_org_id).fetch()
        history = OrderSmsHistory.query(OrderSmsHistory.company == company.key) \
                                 .order(-OrderSmsHistory.sent).fetch(10)
        self.render('/mt/sms_admin.html', company=company, user=self.user, orders=orders, history=history,
                    confirmation_text=_CONFIRMATION_TEXT)

    @push_admin_user_required
    def post(self):
        order_id = self.request.get_range('order_id')
        order = Order.get_by_id(order_id)
        customer_phone = filter_phone(order.customer.get().phone)[1:]

        sms_text = _CONFIRMATION_TEXT % order.number

        success, _ = sms_pilot.send_sms("INFORM", [customer_phone], sms_text)
        OrderSmsHistory(
            order=order.key,
            text=sms_text,
            phone=customer_phone,
            company=self.user.company,
            success=success
        ).put()
        time.sleep(1)

        self.redirect(self.request.uri)

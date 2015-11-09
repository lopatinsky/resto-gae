# coding=utf-8
import logging
from handlers.api.base import BaseHandler
from methods.email import mandrill
from models.iiko import Order
from models.iiko.company import CompanyNew
from models.iiko.order import OrderRate

__author__ = 'dvpermyakov'


class OrderReviewHandler(BaseHandler):
    def post(self, order_id):
        order = Order.order_by_id(order_id)
        meal_rate = float(self.request.get('meal_rate'))
        service_rate = float(self.request.get('service_rate'))
        comment = self.request.get('comment')
        rate = OrderRate(meal_rate=meal_rate, service_rate=service_rate, comment=comment)
        order.rate = rate
        order.put()

        is_negative = 0 < meal_rate < 4 or 0 < service_rate < 4
        if is_negative or rate.comment:
            company = CompanyNew.get_by_iiko_id(order.venue_id)
            customer = order.customer.get()
            body = u"Клиент: %s %s<br>" \
                   u"Заказ №%s<br>" \
                   u"Оценка еды: %d из 5<br>" \
                   u"Оценка обслуживания: %d из 5<br>" % \
                   (customer.phone, customer.name, order.number, meal_rate, service_rate)
            if comment:
                body += u"Комментарий: %s" % comment
            logging.info(body)
            # to = company.support_emails
            # cc = ['mdburshteyn@gmail.com', 'isparfenov@gmail.com']
            to = ['mdburshteyn@gmail.com']
            cc = []
            subject = u'Негативный отзыв о заказе' if is_negative else u'Отзыв о заказе с комментарием'
            mandrill.send_email('noreply-rating@ru-beacon.ru', to, cc, subject, body)

        self.render_json({})

# coding=utf-8
from google.appengine.api import taskqueue

from base import BaseHandler
from random import randint
from models import iiko
from lib import twilio
from datetime import datetime, timedelta


CLOSE_CONFIRMATION_AFTER_MINUTES = 15


class RequestCodeHandler(BaseHandler):
    def post(self):
        customer_id = self.request.get('customer_id')
        phone = self.request.get('phone')
        customer = iiko.Customer.customer_by_customer_id(customer_id)
        if not customer or not phone:
            self.abort(400)
        code = randint(1000, 9999)
        customer.confirmations.append(iiko.AvailableConfirmation(requested_phone=phone, code=code))
        customer.put()
        sms_text = u'Код для подтверждения %s телефона: %s' % (phone, code)
        twilio.send_sms([phone], sms_text)
        closing = datetime.utcnow() + timedelta(minutes=CLOSE_CONFIRMATION_AFTER_MINUTES)
        taskqueue.add(url='/promo_phone/close_confirmation', method='POST', eta=closing, params={
            'customer_id': customer_id,
            'phone': phone
        })
        self.render_json({
            'success': True,
            'text': u'Код для подстверждения доступен в течении 15 минут'
        })


class ConfirmHandler(BaseHandler):
    def send_error(self, description):
        self.response.set_status(400)
        self.render_json({
            'success': False,
            'description': description
        })

    def post(self):
        customer_id = self.request.get('customer_id')
        phone = self.request.get('phone')
        code = self.request.get_range('code')
        customer = iiko.Customer.customer_by_customer_id(customer_id)
        if not customer or not phone or not code:
            self.abort(400)
        confirmation = None
        for avail_confirmation in customer.confirmations:
            if avail_confirmation.requested_phone == phone:
                if avail_confirmation.code != code:
                    return self.send_error(u'Коды не совпадают')
                confirmation = avail_confirmation
                break
        if not confirmation:
            return self.send_error(u'Для данного номер не существует кода')
        customer.confirmed_phones.append(phone)
        customer.confirmations.remove(confirmation)
        customer.put()
        self.render_json({
            'success': True
        })
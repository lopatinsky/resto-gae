# coding=utf-8

import logging
import random
from .base import BaseHandler
from methods.alfa_bank import tie_card, check_status, get_back_blocked_sum, create_pay, pay_by_card, unbind_card
from models.iiko import Company


class AlfaBaseHandler(BaseHandler):
    company = None

    def dispatch(self):
        ua = self.request.headers["User-Agent"]
        name = ua.split('/', 1)[0].lower().strip()
        self.company = Company.query(Company.app_name == name).get()
        if not self.company:
            self.abort(400)
        return super(BaseHandler, self).dispatch()


class PreCheckHandler(AlfaBaseHandler):
    def post(self):
        client_id = self.request.get('clientId')
        amount = self.request.get_range('amount', min_value=100, default=100)
        return_url = self.request.get('returnUrl')

        order_number = random.randrange(1000000000000, 9999999999999)
        tie = tie_card(self.company, amount, order_number, return_url, client_id, 'MOBILE')
        logging.info(str(tie))
        return self.render_json({
            'result': {
                'orderId': tie['orderId'],
                'formUrl': tie['formUrl']
            },
            'error_code': int(tie.get('errorCode', 0))
        })


class CheckStatusHandler(AlfaBaseHandler):
    def post(self):
        order_id = self.request.get('orderId')
        check = check_status(self.company, order_id)
        logging.info(str(check))
        # if check['ErrorCode'] == "2":
        #     sender_email = "Empatika-resto Support <info@resto.com>"
        #     subject = "Error on binding"
        #     client = Customer.customer_by_customer_id(check['clientId'])
        #     body = """
        #
        #     Error on binding card %s.
        #
        #     Message: %s
        #
        #     Client id: %s
        #
        #     Client phone: %s
        #     Client name: %s
        #     """ % (check['Pan'][-4:], check['ErrorMessage'], check['clientId'], client.phone, client.name)
        #
        #     mail.send_mail(sender_email, 'ramazanovrustem@gmail.com', subject, body)

        if check.get('ErrorCode', '0') == '0':
            return self.render_json({
                'result': {
                    'bindingId': check['bindingId'],
                    'pan': check['Pan'],
                    'expiration': check['expiration'],
                    'orderStatus': check['OrderStatus']
                },
                'error_code': int(check.get('ErrorCode', 0)),
            })
        else:
            return self.render_json({
                'error_code': int(check.get('ErrorCode', 0))
            })


class CreateByCardHandler(AlfaBaseHandler):
    def post(self):
        order_id = self.request.get('orderId')
        binding_id = self.request.get('bindingId')
        pay = create_pay(self.company, binding_id, order_id)
        logging.info(str(pay))
        return self.render_json({
            'result': {},
            'error_code': int(pay.get('errorCode', 0)),
        })


class ResetBlockedSumHandler(AlfaBaseHandler):
    def post(self):
        order_id = self.request.get('orderId')
        tie = get_back_blocked_sum(self.company, order_id)
        logging.info(str(tie))
        return self.render_json({
            'result': {},
            'error_code': int(tie.get('errorCode', 0)),
        })


class PayByCardHandler(AlfaBaseHandler):
    def post(self):
        order_id = self.request.get('orderId')
        amount = self.request.get('amount', 0)
        pay = pay_by_card(self.company, order_id, amount)
        logging.info(str(pay))
        return self.render_json({'result': pay})


class UnbindCardHandler(AlfaBaseHandler):
    def post(self):
        binding_id = self.request.get('bindingId')
        unbind = unbind_card(self.company, binding_id)
        logging.info(str(unbind))
        return self.render_json({'result': unbind})

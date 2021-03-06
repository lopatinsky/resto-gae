# coding=utf-8

import logging
import random
from .base import BaseHandler
from methods.alfa_bank import tie_card, check_status, get_back_blocked_sum, create_pay, pay_by_card, unbind_card
from models.iiko import CompanyNew


class AlfaBaseHandler(BaseHandler):
    company = None

    def dispatch(self):
        company_id = self.request.get("organizationId")
        if company_id:
            self.company = CompanyNew.get_by_id(int(company_id))
        if not self.company:
            ua = self.request.headers["User-Agent"]
            name = ua.split('/', 1)[0].lower().strip()
            self.company = CompanyNew.query(CompanyNew.app_name == name).get()
        if not self.company:
            self.abort(400)
        return super(AlfaBaseHandler, self).dispatch()


class PreCheckHandler(AlfaBaseHandler):
    def post(self):
        client_id = self.request.get('clientId')
        amount = self.request.get_range('amount', min_value=100, default=100)
        return_url = self.request.get('returnUrl')

        order_number = random.randrange(1000000000000, 9999999999999)
        tie = tie_card(self.company, None, amount, order_number, return_url, client_id, 'MOBILE')
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
        check = check_status(self.company, None, order_id)
        logging.info(str(check))

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
        pay = create_pay(self.company, None, binding_id, order_id)
        logging.info(str(pay))
        return self.render_json({
            'result': {},
            'error_code': int(pay.get('errorCode', 0)),
        })


class ResetBlockedSumHandler(AlfaBaseHandler):
    def post(self):
        order_id = self.request.get('orderId')
        tie = get_back_blocked_sum(self.company, None, order_id)
        logging.info(str(tie))
        return self.render_json({
            'result': {},
            'error_code': int(tie.get('errorCode', 0)),
        })


class PayByCardHandler(AlfaBaseHandler):
    def post(self):
        order_id = self.request.get('orderId')
        amount = self.request.get('amount', 0)
        pay = pay_by_card(self.company, None, order_id, amount)
        logging.info(str(pay))
        return self.render_json({'result': pay})


class UnbindCardHandler(AlfaBaseHandler):
    def post(self):
        binding_id = self.request.get('bindingId')
        unbind = unbind_card(self.company, binding_id)
        logging.info(str(unbind))
        return self.render_json({'result': unbind})

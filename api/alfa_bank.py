import logging
import random
from google.appengine.api import mail
from api import BaseHandler
from iiko import tie_card, check_status, get_back_blocked_sum, create_pay, pay_by_card, unbind_card, Customer

__author__ = 'mihailnikolaev'

LOGIN = 'empatika_autopay-api'
PASSWORD = 'empatika_autopay'


class PreCheckHandler(BaseHandler):
    def post(self):
        client_id = self.request.get('clientId')
        amount = self.request.get('amount', 100)
        returnUrl = self.request.get('returnUrl')

        order_number = random.randrange(1000000000000, 9999999999999)
        tie = tie_card(LOGIN, PASSWORD, amount, order_number,
                       returnUrl, client_id, 'MOBILE')
        logging.info(str(tie))
        return self.render_json({'result': {'orderId': tie['orderId'],
                                            'formUrl': tie['formUrl']},
                                 'error_code': int(tie.get('errorCode', 0))
                                })


class CheckStatusHandler(BaseHandler):
    def post(self):
        order_id = self.request.get('orderId')
        check = check_status(LOGIN, PASSWORD, order_id)
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
            return self.render_json({'result': {'bindingId': check['bindingId'],
                                            'pan': check['Pan'],
                                            'expiration': check['expiration'],
                                            'orderStatus': check['OrderStatus']},
                                 'error_code': int(check.get('ErrorCode', 0)),
                                })
        else:
            return self.render_json({'error_code': int(check.get('ErrorCode', 0))})


class CreateByCardHandler(BaseHandler):
    def post(self):
        order_id = self.request.get('orderId')
        binding_id = self.request.get('bindingId')
        pay = create_pay(LOGIN, PASSWORD, binding_id, order_id)
        logging.info(str(pay))
        return self.render_json({'result': {},
                                 'error_code': int(pay.get('errorCode', 0)),
                                })


class ResetBlockedSumHandler(BaseHandler):
    def post(self):
        order_id = self.request.get('orderId')
        tie = get_back_blocked_sum(LOGIN, PASSWORD, order_id)
        logging.info(str(tie))
        return self.render_json({'result': {},
                                 'error_code': int(tie.get('errorCode', 0)),
                                })


class PayByCardHandler(BaseHandler):
    def post(self):
        order_id = self.request.get('orderId')
        amount = self.request.get('amount', 0)
        pay = pay_by_card(LOGIN, PASSWORD, order_id, amount)
        logging.info(str(pay))
        return self.render_json({'result': pay})


class UnbindCardHandler(BaseHandler):
    def post(self):
        binding_id = self.request.get('bindingId')
        unbind = unbind_card(LOGIN, PASSWORD, binding_id)
        logging.info(str(unbind))
        return self.render_json({'result': unbind})
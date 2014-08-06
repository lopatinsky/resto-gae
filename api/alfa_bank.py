import random
from google.appengine.api import mail
from api import BaseHandler
from iiko import tie_card, check_status, get_back_blocked_sum, create_pay, pay_by_card, unbind_card, Customer

__author__ = 'mihailnikolaev'

LOGIN = 'empatika_autopay-api'
PASSWORD = 'empatika_autopay'


class PreCheckHandler(BaseHandler):
    def get(self):
        client_id = self.request.get('client_id')
        amount = self.request.get('amount', 100)
        returnUrl = self.request.get('return_url')

        order_number = random.randrange(1000000000000, 9999999999999)
        print order_number
        tie = tie_card(LOGIN, PASSWORD, amount, order_number,
                       returnUrl, client_id, 'DESKTOP')
        return self.render_json({'id': tie})


class CheckStatusHandler(BaseHandler):
    def get(self):
        order_id = self.request.get('orderId')
        check = check_status(LOGIN, PASSWORD, order_id)
        if check['ErrorCode'] == "2":
            sender_email = "Empatika-resto Support <info@resto.com>"
            subject = "Error on binding"
            client = Customer.customer_by_customer_id(check['clientId'])
            body = """

            Error on binding card %s.

            Message: %s

            Client id: %s

            Client phone: %s
            Client name: %s
            """ % (check['Pan'][-4:], check['ErrorMessage'], check['clientId'], client.phone, client.name)

            mail.send_mail(sender_email, 'ramazanovrustem@gmail.com', subject, body)

        return self.render_json({"result": check})


class CreateByCardHandler(BaseHandler):
    def post(self):
        order_id = self.request.get('order_id')
        binding_id = self.request.get('binding_id')
        pay = create_pay(LOGIN, PASSWORD, binding_id, order_id)
        if pay['errorCode'] == 0:
            return self.render_json({"code": pay['errorCode']})
        else:
            return self.render_json({"code": pay['errorCode']})


class ResetBlockedSumHandler(BaseHandler):
    def post(self):
        order_id = self.request.get('order_id')
        tie = get_back_blocked_sum(LOGIN, PASSWORD, order_id)
        if tie['errorCode'] == "0":
            return self.render_json({"code": tie['errorCode']})
        else:
            return self.render_json({"code": tie['errorCode']})


class PayByCardHandler(BaseHandler):
    def post(self):
        order_id = self.request.get('order_id')
        amount = self.request.get('amount', 0)
        pay = pay_by_card(LOGIN, PASSWORD, order_id, amount)
        if pay['errorCode'] == "0":
            return self.render_json({"code": pay['errorCode']})
        else:
            return self.render_json({"code": pay['errorCode']})


class UnbindCardHandler(BaseHandler):
    def post(self):
        binding_id = self.request.get('binding_id')
        unbind = unbind_card(LOGIN, PASSWORD, binding_id)
        if unbind['errorCode'] == "0":
            return self.render_json({"code": unbind['errorCode']})
        else:
            return self.render_json({"code": unbind['errorCode']})
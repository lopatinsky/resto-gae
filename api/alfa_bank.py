import random
from api import BaseHandler
from iiko import tie_card, check_status, get_back_blocked_sum

__author__ = 'mihailnikolaev'

LOGIN = 'empatika_autopay-api'
PASSWORD = 'empatika_autopay'


class PreCheckHandler(BaseHandler):
    def get(self):
        client_id = self.request.get('client_id')

        order_number = random.randrange(1000000000000, 9999999999999)
        print order_number
        tie = tie_card(LOGIN, PASSWORD, 100, order_number,
                       'http://127.0.0.1:8080/api/alfa/binding', client_id, 'DESKTOP')
        return self.render_json({'id': tie})


class TieCardHandler(BaseHandler):
    def get(self):
        order_id = self.request.get('orderId')
        tie = check_status(LOGIN, PASSWORD, order_id)

        binding_id = ""
        if tie['OrderStatus'] == 1 and tie['ErrorCode'] == "0":
            binding_id = tie['bindingId']
        print 'binding %s' % binding_id
        tie = get_back_blocked_sum(LOGIN, PASSWORD, order_id)

        if tie['errorCode'] == "0":

            check = check_status(LOGIN, PASSWORD, order_id)
            if check['OrderStatus'] == 3 and check['ErrorCode'] == "0":
                print binding_id
                return self.render_json({"id": binding_id})
            else:
                return self.render_json({"error": "Unable to unblock"})
        else:
            return self.render_json({"error": "Unable to unblock"})
from webapp2 import RequestHandler
from methods.iiko.customer import get_customer_by_phone
from models.iiko import Order, CompanyNew
from models.specials import SharedBonus

__author__ = 'dvpermyakov'


class SharedBonusActivateHandler(RequestHandler):
    def post(self):
        order_id = self.request.get('order_id')
        order = Order.order_by_id(order_id)
        company = CompanyNew.get_by_iiko_id(order.venue_id)
        customer = order.customer.get()
        bonus = SharedBonus.query(SharedBonus.recipient == order.customer, SharedBonus.status == SharedBonus.READY).get()
        iiko_history = get_customer_by_phone(company, customer.phone)
        order_found = False
        if iiko_history.get('customersDeliveryHistory'):
            for customer_info in iiko_history["customersDeliveryHistory"]:
                if customer_info.get("deliveryHistory"):
                    bonus.cancel()
                    order_found = True
        if iiko_history.get('historyOrders'):
            bonus.cancel()
            order_found = True
        if not order_found:
            bonus.deactivate(company)

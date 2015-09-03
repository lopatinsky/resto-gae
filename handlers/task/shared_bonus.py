from webapp2 import RequestHandler
from methods.iiko.history import get_history_by_phone
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
        iiko_history = get_history_by_phone(customer.phone, company.iiko_org_id)
        order_count = 0
        if iiko_history.get('customersDeliveryHistory'):
            for customer_info in iiko_history["customersDeliveryHistory"]:
                if customer_info.get("deliveryHistory"):
                    order_count += len(customer_info['deliveryHistory'])
        if order_count == 1:
            bonus.deactivate(company)
        else:
            bonus.cancel()

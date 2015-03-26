import webapp2
from models import iiko


class CloseConfirmationHandler(webapp2.RequestHandler):
    def post(self):
        customer_id = self.request.get('customer_id')
        phone = self.request.get('phone')
        customer = iiko.Customer.customer_by_customer_id(customer_id)
        confirmation = None
        for avail_confirmation in customer.confirmations:
            if avail_confirmation.requested_phone == phone:
                confirmation = avail_confirmation
                break
        if confirmation:
            customer.confirmations.remove(confirmation)
            customer.put()
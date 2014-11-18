import webapp2
from cron.update_menu import UpdateMenuHandler
from cron.update_orders import UpdateOrdersHandler

app = webapp2.WSGIApplication([
    ('/cron/update_orders', UpdateOrdersHandler),
    ('/cron/update_menu', UpdateMenuHandler)
], debug=True)

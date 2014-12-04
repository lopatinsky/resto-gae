# coding=utf-8

import webapp2
from cron.update_menu import UpdateMenuHandler
from cron.update_orders import UpdateOrdersHandler
from cron.mivako_gifts import MivakoGiftsEmailHandler

app = webapp2.WSGIApplication([
    ('/cron/update_orders', UpdateOrdersHandler),
    ('/cron/update_menu', UpdateMenuHandler),
    ('/cron/mivako_gifts', MivakoGiftsEmailHandler),
], debug=True)

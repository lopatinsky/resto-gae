# coding=utf-8

import webapp2
from .update_menu import UpdateMenuHandler
from .update_orders import UpdateOrdersHandler
from .mivako_gifts import MivakoGiftsEmailHandler
from .coffee_city_updates import CoffeeCityUpdatesHandler, CheckCoffeeCityUpdatesHandler

app = webapp2.WSGIApplication([
    ('/cron/update_orders', UpdateOrdersHandler),
    ('/cron/update_menu', UpdateMenuHandler),
    ('/cron/mivako_gifts', MivakoGiftsEmailHandler),

    ('/cron/check_coffee_city', CheckCoffeeCityUpdatesHandler),
    ('/task/update_coffee_city', CoffeeCityUpdatesHandler),
], debug=True)

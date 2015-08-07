# coding=utf-8

import webapp2
from .update_menu import UpdateMenuHandler, UpdateMenuImagesHandler
from .update_orders import UpdateOrdersHandler
from .mivako_gifts import MivakoGiftsEmailHandler
from .coffee_city_updates import CoffeeCityUpdatesHandler, CheckCoffeeCityUpdatesHandler
from build_square_table import BuildSquareTableHandler

app = webapp2.WSGIApplication([
    ('/cron/update_orders', UpdateOrdersHandler),
    ('/cron/update_menu', UpdateMenuHandler),
    ('/cron/update_menu_images', UpdateMenuImagesHandler),
    ('/cron/mivako_gifts', MivakoGiftsEmailHandler),
    ('/cron/build_square_table', BuildSquareTableHandler),
    ('/cron/check_coffee_city', CheckCoffeeCityUpdatesHandler),
    ('/task/update_coffee_city', CoffeeCityUpdatesHandler),
], debug=True)

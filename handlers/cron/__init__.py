# coding=utf-8

import webapp2

from handlers.cron.creating_orders import CheckCreatingOrdersHandler
from handlers.cron.fast_updates import FastUpdatesHandler
from .build_square_table import BuildSquareTableHandler
from .inactive_clients import InactiveClientsWithPromo
from .mivako_gifts import MivakoGiftsEmailHandler
from .oe_recommendations import BuildRecommendationsHandler
from .update_menu import UpdateMenuHandler, UpdateMenuImagesHandler
from .update_orders import UpdateOrdersHandler
from .update_stop_lists import UpdateStopListsHandler
from .update_streets import UpdateStreetsHandler

app = webapp2.WSGIApplication([
    ('/cron/update_orders', UpdateOrdersHandler),
    ('/cron/update_menu', UpdateMenuHandler),
    ('/cron/update_menu_images', UpdateMenuImagesHandler),
    ('/cron/mivako_gifts', MivakoGiftsEmailHandler),
    ('/cron/build_square_table', BuildSquareTableHandler),
    ('/cron/inactive_clients', InactiveClientsWithPromo),
    ('/cron/update_streets', UpdateStreetsHandler),
    ('/cron/build_recommendations', BuildRecommendationsHandler),
    ('/cron/update_stop_lists', UpdateStopListsHandler),
    ('/cron/fast_updates', FastUpdatesHandler),
    ('/cron/creating_orders', CheckCreatingOrdersHandler),
])

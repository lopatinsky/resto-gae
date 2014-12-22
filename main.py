# coding=utf-8

import webapp2
from api import *
from api import specials


app = webapp2.WSGIApplication([
    # payment
    ('/api/alfa/registration', PreCheckHandler),
    ('/api/alfa/check', CheckStatusHandler),
    ('/api/alfa/create', CreateByCardHandler),
    ('/api/alfa/reset', ResetBlockedSumHandler),
    ('/api/alfa/pay', PayByCardHandler),
    ('/api/alfa/unbind', UnbindCardHandler),

    # company info
    ('/api/venues/(.*)', VenuesHandler),
    ('/api/delivery_types', GetAvailableDeliveryTypesHandler),

    # venue
    ('/api/venue/(.*)/menu', MenuHandler),
    ('/api/payment_types/(.*)', GetPaymentTypesHandler),
    ('/api/venue/(.*)/order/new', PlaceOrderHandler),
    ('/api/venue/(.*)/new_orders', VenueNewOrderListHandler),
    ('/api/check_delivery', GetDeliveryRestrictionsHandler),
    ('/api/iiko_promos', GetVenuePromosHandler),

    # order info
    ('/api/history', HistoryHandler),
    ('/api/venue/(.*)/order/(.*)', VenueOrderInfoRequestHandler),
    ('/api/order/(.*)', OrderInfoRequestHandler),
    ('/api/status', OrdersStatusHandler),
    ('/api/get_orders_with_bonuses', GetOrdersWithBonusesHandler),
    ('/api/get_order_promo', GetOrderPromosHandler),

    # utility
    ('/api/address', AddressInputHandler),
    ('/api/get_info', GetAddressByKeyHandler),

    # specials
    ('/api/specials/mivako_gift/info', specials.MivakoPromoInfoHandler),
    ('/api/specials/mivako_gift/send', specials.MivakoPromoSendGiftHandler),

    ('/img/(.*)', ImageProxyHandler),
], debug=True)

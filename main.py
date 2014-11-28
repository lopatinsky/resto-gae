#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import webapp2
from api import *
from api import specials


class MainHandler(webapp2.RequestHandler):
    def get(self):
        pass


app = webapp2.WSGIApplication([
    ('/api/venues/(.*)', VenuesHandler),
    ('/api/venue/(.*)/menu', MenuRequestHandler),
    ('/api/alfa/registration', PreCheckHandler),
    ('/api/alfa/check', CheckStatusHandler),
    ('/api/alfa/create', CreateByCardHandler),
    ('/api/alfa/reset', ResetBlockedSumHandler),
    ('/api/alfa/pay', PayByCardHandler),
    ('/api/alfa/unbind', UnbindCardHandler),
    ('/api/history', HistoryRequestHandler),
    ('/api/address', AddressInputRequestHandler),
    ('/api/get_info', GetInfoRequestHandler),
    ('/api/check_delivery', GetDeliveryRestrictionsRequestHandler),
    ('/api/venue/(.*)/order/new', PlaceOrderRequestHandler),
    ('/api/venue/(.*)/order/(.*)', VenueOrderInfoRequestHandler),
    ('/api/order/(.*)', OrderInfoRequestHandler),
    ('/api/venue/(.*)/new_orders', VenueNewOrderListHandler),
    ('/api/status', StatusRequestHandler),
    ('/api/add_company', AddCompanyRequestHandler),
    ('/api/payment_types/(.*)', GetPaymentType),
    ('/api/payment_type/add', AddPaymentType),
    ('/api/payment_type/edit', EditPaymentType),
    ('/api/delivery_types', GetAvailableDeliveryTypesHandler),
    ('/api/delivery_type/add', AddDeliveryType),
    ('/api/get_orders_with_bonuses', GetOrdersWithBonuses),

    ('/api/specials/mivako_gift/info', specials.MivakoPromoInfoHandler),
    ('/api/specials/mivako_gift/send', specials.MivakoPromoSendGiftHandler),

    ('/img/(.*)', ImageProxyHandler),
    ('/', MainHandler)
], debug=True)

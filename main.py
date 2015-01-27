# coding=utf-8

import webapp2
from api import *
from api import specials
from mt import CreateCompaniesLinks, CompanySettingsHandler, report


app = webapp2.WSGIApplication([
    # payment
    ('/api/alfa/registration', PreCheckHandler),
    ('/api/alfa/check', CheckStatusHandler),
    ('/api/alfa/create', CreateByCardHandler),
    ('/api/alfa/reset', ResetBlockedSumHandler),
    ('/api/alfa/pay', PayByCardHandler),
    ('/api/alfa/unbind', UnbindCardHandler),

    # company creating
    ('/api/company/create_or_update', CreateOrUpdateCompanyHandler),
    ('/api/company/set_icons', UploadIconsHandler),

    # company info
    ('/api/company/(\d+)/info', GetCompanyInfoHandler),
    ('/api/venues/(.*)', VenuesHandler),
    ('/api/delivery_types', GetAvailableDeliveryTypesHandler),
    ('/api/company/(\d+)/user_data', SaveClientInfoHandler),
    ('/api/company/get_company', GetCompanyHandler),
    ('/api/company/all_companies', GetCompaniesHandler),
    ('/api/company/get_icons', DownloadIconsHandler),

    # maintenance
    ('/mt/company/links', CreateCompaniesLinks),
    ('/mt/company/settings/(.*)', CompanySettingsHandler),
    # reports
    ('/mt/report', report.ReportHandler),
    ('/mt/report/venues', report.VenueReportHandler),
    ('/mt/report/orders', report.OrdersReportHandler),
    ('/mt/report/clients', report.ClientsReportHandler),
    ('/mt/report/repeated_orders', report.RepeatedOrdersReportHandler),

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

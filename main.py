# coding=utf-8
from google.appengine.api import app_identity
import sys

import webapp2
from api import *
from api import admin, specials
from api import push_admin as api_push_admin
from config import config
from methods import email
from mt import CreateCompaniesLinks, CompanySettingsHandler, report, push_admins, push, migration
from webapp2 import Route
import share
from api import promo_phone
import tasks


_APP_ID = app_identity.get_application_id()


def handle_500(request, response, exception):
    body = """URL: %s
User-Agent: %s
Exception: %s
Logs: https://appengine.google.com/logs?app_id=s~%s&severity_level_override=0&severity_level=3""" \
           % (request.url, request.headers['User-Agent'], exception, _APP_ID)
    email.send_error("server", "Error 500", body)

    exc_info = sys.exc_info()
    raise exc_info[0], exc_info[1], exc_info[2]


class MainHandler(webapp2.RequestHandler):
    def get(self):
        self.redirect("http://ru-beacon.ru/")

webapp2_config = {
    "webapp2_extras.sessions": {
        "secret_key": '\xfe\xc1\x1d\xc0+\x10\x11\x9a\x0b\xe6\xeb\xd5e \x85NgZ\xcbL\xee\xb0p~\x08\xd5\xa5\x1bAc\x88/'
                      '\xae\t@\xdc\x08d\xe9\xdb'
    },
    "webapp2_extras.auth": {
        "user_model": "models.admin.User"
    }
}

app = webapp2.WSGIApplication([
    # customer
    ('/api/customer/register', RegisterHandler),

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
    ('/api/company/(\d+)/menu', CompanyMenuHandler),
    ('/api/company/(\d+)/payment_types', CompanyPaymentTypesHandler),
    ('/api/company/(\d+)/promos', CompanyPromosHandler),
    ('/api/venues/(.*)', VenuesHandler),
    ('/api/delivery_types', GetAvailableDeliveryTypesHandler),
    ('/api/company/(\d+)/user_data', SaveClientInfoHandler),
    ('/api/company/get_company', GetCompanyHandler),
    ('/api/company/all_companies', GetCompaniesHandler),
    ('/api/company/get_icons', DownloadIconsHandler),

    # admin
    ('/api/admin/orders/current', admin.CurrentOrdersHandler),
    ('/api/admin/orders/updates', admin.OrderUpdatesHandler),
    ('/api/admin/orders/cancels', admin.CancelsHandler),
    ('/api/admin/orders/closed', admin.ClosedOrdersHandler),
    ('/api/admin/login', admin.LoginHandler),
    ('/api/admin/logout', admin.LogoutHandler),

    # push_admin
    Route('/api/push_admin/login', api_push_admin.LoginHandler, 'push_admin_login'),
    Route('/api/push_admin/logout', api_push_admin.LogoutHandler),
    Route('/api/push_admin/pushes', api_push_admin.PushSendingHandler, 'pushes'),
    Route('/api/push_admin/history', api_push_admin.PushHistoryHandler, 'admin_push_history'),

    # maintenance
    ('/mt/company/links', CreateCompaniesLinks),
    ('/mt/company/settings/(.*)', CompanySettingsHandler),
    ('/mt/push/send', push.PushSendingHandler),
    Route('/mt/push/history', push.PushHistoryHandler, 'mt_push_history'),
    # push_admin
    ('/mt/push_admin/create_admins', push_admins.AutoCreatePushAdmins),
    Route('/mt/push_admin/list', push_admins.ListPushAdmins, 'push_admin_main'),
    Route('/mt/push_admin/<admin_id:\d+>/change_login', push_admins.ChangeLoginPushAdmin),
    Route('/mt/push_admin/<admin_id:\d+>/change_password', push_admins.ChangePasswordPushAdmin),
    # reports
    ('/mt/report', report.ReportHandler),
    ('/mt/report/venues', report.VenueReportHandler),
    ('/mt/report/orders', report.OrdersReportHandler),
    ('/mt/report/clients', report.ClientsReportHandler),
    ('/mt/report/repeated_orders', report.RepeatedOrdersReportHandler),
    ('/mt/report/square_table', report.SquareTableHandler),

    ('/mt/migrate', migration.CreateNewCompaniesHandler),

    # venue
    ('/api/venue/(.*)/menu', MenuHandler),
    ('/api/payment_types/(.*)', GetPaymentTypesHandler),
    ('/api/venue/(.*)/order/new', PlaceOrderHandler),
    ('/api/iiko_promos', GetVenuePromosHandler),
    ('/api/promo_phone/request_code', promo_phone.RequestCodeHandler),
    ('/api/promo_phone/confirm', promo_phone.ConfirmHandler),

    # order info
    ('/api/history', HistoryHandler),
    ('/api/order/(.*)/request_cancel', OrderRequestCancelHandler),
    ('/api/order/(.*)', OrderInfoRequestHandler),
    ('/api/status', OrdersStatusHandler),
    ('/api/get_order_promo', GetOrderPromosHandler),

    # utility
    ('/api/address', AddressInputHandler),
    ('/api/get_info', GetAddressByKeyHandler),

    # specials
    ('/api/specials/mivako_gift/info', specials.MivakoPromoInfoHandler),
    ('/api/specials/mivako_gift/send', specials.MivakoPromoSendGiftHandler),
    ('/api/specials/cat_add_social', specials.CATAddSocialHandler),
    ('/api/specials/cat_places', specials.CATFetchCoffeeShopsHandler),
    ('/api/specials/cat_company_id', specials.CATGetCompanyIdHandler),
    ('/api/specials/cat_company_id_2', specials.CATGetCompanyIdHandler2),

    webapp2.Route('/get/<app:[a-z]{,3}>', share.GATrackDownloadHandler),

    # branch_features
    ('/shared/invitation/get_url', specials.GetInvitationUrlsHandler),
    ('/shared/gift/get_url', specials.GetGiftUrlsHandler),

    ('/img/(.*)', ImageProxyHandler),

    ('/', MainHandler),
    ('/promo_phone/close_confirmation', tasks.CloseConfirmationHandler),
], debug=config.DEBUG, config=webapp2_config)

app.error_handlers[500] = handle_500

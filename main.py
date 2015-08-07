# coding=utf-8
from webapp2_extras.routes import PathPrefixRoute
from webapp2 import Route, WSGIApplication

from handlers import handle_500, iikobiz, share
from handlers import api
from handlers.api import admin, specials, alfa_bank, image_proxy, push_admin as api_push_admin, address, order, company, \
    venue, customer, promos
from handlers.mt import report, push_admins, migration, qr, changes, company as mt_company
from handlers.mt import push
from config import config
import trash

webapp2_config = {
    "webapp2_extras.sessions": {
        "secret_key": '\xfe\xc1\x1d\xc0+\x10\x11\x9a\x0b\xe6\xeb\xd5e \x85NgZ\xcbL\xee\xb0p~\x08\xd5\xa5\x1bAc\x88/'
                      '\xae\t@\xdc\x08d\xe9\xdb'
    },
    "webapp2_extras.auth": {
        "user_model": "models.admin.User"
    }
}

app = WSGIApplication([
    Route('/', api.MainHandler),

    PathPrefixRoute('/api', [

        PathPrefixRoute('/alfa', [
            Route('/registration', alfa_bank.PreCheckHandler),
            Route('/check', alfa_bank.CheckStatusHandler),
            Route('/create', alfa_bank.CreateByCardHandler),
            Route('/reset', alfa_bank.ResetBlockedSumHandler),
            Route('/pay', alfa_bank.PayByCardHandler),
            Route('/unbind', alfa_bank.UnbindCardHandler),
        ]),

        PathPrefixRoute('/company', [
            PathPrefixRoute('/<company_id:\d+>', [
                Route('/info', api.NewsHandler),
                Route('/menu', company.CompanyMenuHandler),
                Route('/payment_types', company.CompanyPaymentTypesHandler),
                Route('/promos', promos.CompanyPromosHandler),
                Route('/user_data', customer.SaveClientInfoHandler),
                Route('/enter_card', customer.SaveBonusCardHandler),
            ]),
            Route('/get_company', company.CompanyInfoHandler),
        ]),
        Route('/delivery_types', company.CompanyDeliveryTypesHandler),                          # it relates to company
        Route('/venues/<company_id:\d+>', company.CompanyVenuesHandler),                        # it relates to company

        PathPrefixRoute('/venue/<delivery_terminal_id:.*>', [
            Route('/menu', venue.VenueMenuHandler),
            Route('/order/new', order.PlaceOrderHandler),
        ]),
        Route('/payment_types/<delivery_terminal_id:.*>', venue.VenuePaymentTypesHandler),       # it relates to venue
        Route('/iiko_promos', promos.VenuePromosHandler),                                        # it relates to venue

        PathPrefixRoute('/order/<order_id:.*>', [
            Route('request_cancel', order.CancelOrderHandler),
            Route('', order.OrderInfoHandler),
        ]),
        Route('/status', order.OrdersStatusHandler),                                             # it relates to order
        Route('/history', order.HistoryHandler),                                                 # it relates to order
        Route('/get_order_promo', order.CheckOrderHandler),                                      # it relates to order

        PathPrefixRoute('/customer', [
            Route('/register', api.RegisterHandler),
        ]),

        PathPrefixRoute('/admin', [
            Route('/login', admin.LoginHandler),
            Route('/logout', admin.LogoutHandler),
            PathPrefixRoute('/orders', [
                Route('/current', admin.CurrentOrdersHandler),
                Route('/updates', admin.OrderUpdatesHandler),
                Route('/cancels', admin.CancelsHandler),
                Route('/closed', admin.ClosedOrdersHandler),
            ]),
            Route('/menu', admin.MenuHandler),
            Route('/dynamic_info', admin.DynamicInfoHandler),
            Route('/stop_list/items', admin.ItemStopListHandler),
            Route('/customer_history', admin.ClientHistoryHandler),
        ]),
        PathPrefixRoute('/push_admin', [
            Route('/login', api_push_admin.LoginHandler, 'push_admin_login'),
            Route('/logout', api_push_admin.LogoutHandler),
            Route('/pushes', api_push_admin.PushSendingHandler, 'pushes'),
            Route('/history', api_push_admin.PushHistoryHandler, 'admin_push_history'),
            Route('/sms', api_push_admin.SmsAdminHandler),
            Route('/menu_reload', api_push_admin.ReloadMenuHandler),
        ]),
        PathPrefixRoute('/specials', [
            PathPrefixRoute('/mivako_gift', [
                Route('/info', specials.MivakoPromoInfoHandler),
                Route('/send', specials.MivakoPromoSendGiftHandler),
            ]),
            Route('/cat_add_social', specials.CATAddSocialHandler),
            Route('/cat_places', specials.CATFetchCoffeeShopsHandler),
            Route('/cat_company_id', specials.CATGetCompanyIdHandler),
            Route('/cat_company_id_2', specials.CATGetCompanyIdHandler2),
        ]),
        Route('/address', address.AddressByStreetHandler),
        Route('/get_info', trash.GetAddressByKeyHandler),
    ]),

    PathPrefixRoute('/mt', [
        PathPrefixRoute('/report', [
            Route('', report.ReportHandler),
            Route('/venues', report.VenueReportHandler),
            Route('/orders', report.OrdersReportHandler),
            Route('/orders_lite', report.OrdersLiteReportHandler),
            Route('/clients', report.ClientsReportHandler),
            Route('/repeated_orders', report.RepeatedOrdersReportHandler),
            Route('/square_table', report.SquareTableHandler),
        ]),
        PathPrefixRoute('/company', [
            Route('/links', mt_company.CreateCompaniesLinks),
            Route('/settings/<:.*>', mt_company.CompanySettingsHandler),
        ]),
        PathPrefixRoute('/push', [
            Route('/send', push.PushSendingHandler),
            Route('/history', push.PushHistoryHandler, 'mt_push_history'),
        ]),
        PathPrefixRoute('/push_admin', [
            Route('/create_admins', push_admins.AutoCreatePushAdmins),
            Route('/list', push_admins.ListPushAdmins, 'push_admin_main'),
            PathPrefixRoute('/<admin_id:\d+>', [
                Route('', push_admins.ChangeLoginPushAdmin),
                Route('/change_password', push_admins.ChangePasswordPushAdmin),
            ]),
        ]),
        PathPrefixRoute('/qr', [
            Route('', qr.AnalyticsLinkListHandler),
            Route('/([a-z]{,3})', qr.AnalyticsLinkEditHandler),
        ]),
        PathPrefixRoute('/changelogs', [
            Route('', changes.ChangeLogFindOrderHandler),
            Route('/<order_id:.*>', changes.ViewChangeLogsHandler, "view_changelog"),
        ]),
        Route('/migrate', migration.CreateNewCompaniesHandler),
    ]),

    PathPrefixRoute('/shared', [
        PathPrefixRoute('/invitation', [
            Route('/get_url', specials.GetInvitationUrlsHandler),
        ]),
        PathPrefixRoute('/gift', [
            Route('/get_url', specials.GetGiftUrlsHandler),
        ]),
    ]),

    Route('/get/<app:[a-z]{,3}>', share.GATrackDownloadHandler),
    Route('/img/<:.*>', image_proxy.ImageProxyHandler),
    Route('/iiko_biz_app', iikobiz.IikoBizAppHandler),
    Route('/iiko_biz_submit', iikobiz.IikoBizSubmitHandler),
], debug=config.DEBUG, config=webapp2_config)

app.error_handlers[500] = handle_500

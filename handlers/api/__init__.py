# coding=utf-8
from webapp2 import RequestHandler
from webapp2_extras import jinja2

from venues import VenuesHandler
from menu import MenuHandler, CompanyMenuHandler
from orders import OrderInfoRequestHandler, PlaceOrderHandler, OrderRequestCancelHandler
from history import HistoryHandler
from status import OrdersStatusHandler
from address_input import AddressInputHandler
from get_info import GetAddressByKeyHandler, GetVenuePromosHandler, GetOrderPromosHandler, GetCompanyInfoHandler, \
    SaveClientInfoHandler, CompanyPromosHandler, GetClientByBonusCardHandler
from payment_type import GetPaymentTypesHandler, CompanyPaymentTypesHandler
from delivery_type import GetAvailableDeliveryTypesHandler
from alfa_bank import CheckStatusHandler, CreateByCardHandler, PayByCardHandler, PreCheckHandler, \
    ResetBlockedSumHandler, UnbindCardHandler
from image_proxy import ImageProxyHandler
from automation import CreateOrUpdateCompanyHandler, GetCompanyHandler, GetCompaniesHandler, UploadIconsHandler,\
    DownloadIconsHandler
from register import RegisterHandler


class MainHandler(RequestHandler):
    def get(self):
        self.response.write(jinja2.get_jinja2(app=self.app).render_template("landing.html"))

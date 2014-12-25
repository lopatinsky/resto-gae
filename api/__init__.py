# coding=utf-8

from venues import VenuesHandler
from menu import MenuHandler
from orders import OrderInfoRequestHandler, PlaceOrderHandler, VenueNewOrderListHandler,\
    VenueOrderInfoRequestHandler
from history import HistoryHandler
from status import OrdersStatusHandler
from address_input import AddressInputHandler
from check_delivery import GetDeliveryRestrictionsHandler
from get_info import GetAddressByKeyHandler, GetVenuePromosHandler, GetOrderPromosHandler, GetCompanyInfoHandler, \
    SaveClientInfoHandler
from payment_type import GetPaymentTypesHandler
from delivery_type import GetAvailableDeliveryTypesHandler
from bonus import GetOrdersWithBonusesHandler
from alfa_bank import CheckStatusHandler, CreateByCardHandler, PayByCardHandler, PreCheckHandler, \
    ResetBlockedSumHandler, UnbindCardHandler
from image_proxy import ImageProxyHandler

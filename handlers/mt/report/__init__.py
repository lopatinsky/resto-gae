# coding=utf-8
from ..base import BaseHandler
from venue import VenueReportHandler
from clients import ClientsReportHandler
from orders import OrdersReportHandler
from orders_lite import OrdersLiteReportHandler
from repeated_orders import RepeatedOrdersReportHandler
from square_table import SquareTableHandler
from sum_order_changes import OrderSumChangesReport

__author__ = 'dvpermyakov'


class ReportHandler(BaseHandler):
    def get(self):
        self.render('reports/list.html')

# coding=utf-8
import datetime
import logging

from webapp2 import RequestHandler
from config import config
from methods.iiko.history import get_orders
from models.iiko import Order, CompanyNew


class FastUpdatesHandler(RequestHandler):
    def get(self):
        today = datetime.datetime.combine(datetime.date.today(), datetime.time())
        tomorrow = today + datetime.timedelta(days=1)
        if config.DEBUG:
            org_ids = [CompanyNew.EMPATIKA]
        else:
            org_ids = [CompanyNew.HLEB]
        for org_id in org_ids:
            try:
                iiko_orders = get_orders(CompanyNew.get_by_iiko_id(org_id), today, tomorrow)['deliveryOrders']
                for order in iiko_orders:
                    Order.load_from_object(order)
            except Exception as e:
                logging.exception(e)

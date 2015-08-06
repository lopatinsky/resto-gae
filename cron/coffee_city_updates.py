# coding=utf-8
import datetime
import logging
from google.appengine.api import taskqueue

from webapp2 import RequestHandler
from config import config
from methods.iiko.history import get_orders
from models.iiko import Order, CompanyNew


class CoffeeCityUpdatesHandler(RequestHandler):
    def get(self):
        today = datetime.datetime.combine(datetime.date.today(), datetime.time())
        tomorrow = today + datetime.timedelta(days=1)
        if config.DEBUG:
            org_ids = [CompanyNew.EMPATIKA, CompanyNew.COFFEE_CITY]
        else:
            org_ids = [CompanyNew.COFFEE_CITY]
        for org_id in org_ids:
            try:
                iiko_orders = get_orders(CompanyNew.get_by_iiko_id(org_id), today, tomorrow)['deliveryOrders']
                for order in iiko_orders:
                    Order.load_from_object(order)
            except Exception as e:
                logging.exception(e)
        taskqueue.add(queue_name='updates', countdown=30, url='/task/update_coffee_city', method='GET')


class CheckCoffeeCityUpdatesHandler(RequestHandler):
    def get(self):
        stats = taskqueue.Queue('updates').fetch_statistics()
        assert isinstance(stats, taskqueue.QueueStatistics)
        if stats.tasks + stats.in_flight == 0:
            taskqueue.add(queue_name='updates', url='/task/update_coffee_city', method='GET')

# coding=utf-8
import datetime
from google.appengine.api import taskqueue

from webapp2 import RequestHandler
from methods import iiko_api
from models.iiko import Order, Venue


class CoffeeCityUpdatesHandler(RequestHandler):
    def get(self):
        today = datetime.datetime.combine(datetime.date.today(), datetime.time())
        tomorrow = today + datetime.timedelta(days=1)
        venue_ids = [Venue.EMPATIKA, Venue.COFFEE_CITY]
        for venue_id in venue_ids:
            iiko_orders = iiko_api.get_orders(Venue.venue_by_id(venue_id), today, tomorrow)['deliveryOrders']
            for order in iiko_orders:
                Order.load_from_object(order)
        taskqueue.add(queue_name='updates', countdown=30, url='/task/update_coffee_city', method='GET')


class CheckCoffeeCityUpdatesHandler(RequestHandler):
    def get(self):
        stats = taskqueue.Queue('updates').fetch_statistics()
        assert isinstance(stats, taskqueue.QueueStatistics)
        if stats.tasks + stats.in_flight == 0:
            taskqueue.add(queue_name='updates', url='/task/update_coffee_city', method='GET')

# coding=utf-8

from api.base import BaseHandler
from methods.maps import get_address_by_key
import json
from methods import iiko_api
from models import iiko
import logging


class GetAddressByKeyHandler(BaseHandler):

    """ /api/get_info """

    def get(self):
        key = self.request.get('key')

        info = get_address_by_key(key)

        return json.loads(self.render_json(info)).get()


class GetVenuePromosHandler(BaseHandler):

    def get(self):
        venue_id = self.request.get_range('venue_id')
        company_id = iiko.Venue.get_by_id(venue_id).company_id
        venue_iiko_id = iiko.Venue.get_by_id(venue_id).venue_id
        token = iiko_api.get_access_token(company_id)
        return self.render_json({"promos": iiko_api.get_venue_promos(venue_iiko_id, token)})


class GetOrderPromosHandler(BaseHandler):

    def get(self):
        order_id = self.request.get_range('order_id')
        order = iiko.Order.get_by_id(order_id)

        venue_iiko_id = order.venue_id
        venue = iiko.Venue.venue_by_id(venue_iiko_id)

        company_id = venue.company_id
        token = iiko_api.get_access_token(company_id)
        return self.render_json({"promos": iiko_api.get_order_promos(order.order_id, token)})

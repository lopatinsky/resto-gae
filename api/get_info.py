# coding=utf-8

from api.base import BaseHandler
from methods.maps import get_address_by_key
import json
from methods import iiko_api
from models import iiko
import datetime
import logging
from models.iiko import Company


class GetAddressByKeyHandler(BaseHandler):

    """ /api/get_info """

    def get(self):
        key = self.request.get('key')

        info = get_address_by_key(key)

        return json.loads(self.render_json(info)).get()


class GetVenuePromosHandler(BaseHandler):

    def get(self):
        venue_id = self.request.get('venue_id')
        company_id = iiko.Venue.venue_by_id(venue_id).company_id
        token = iiko_api.get_access_token(company_id)
        return self.render_json({"promos": iiko_api.get_venue_promos(venue_id, token)})


class GetOrderPromosHandler(BaseHandler):

    def post(self):
        venue_id = self.request.get('venue_id')
        name = self.request.get('name').strip()
        phone = self.request.get('phone')
        if len(phone) == 10 and not phone.startswith("7"):  # old Android version
            phone = "7" + phone
        customer_id = self.request.get('customer_id')
        order_sum = self.request.get('sum')

        customer = iiko.Customer.customer_by_customer_id(customer_id)
        if not customer:
            customer = iiko.Customer()
            customer.phone = phone
            customer.name = name
            if customer_id:
                customer.customer_id = customer_id
            customer.put()

        order = iiko.Order()
        order.sum = float(order_sum)
        order.date = datetime.datetime.fromtimestamp(int(self.request.get('date')))
        order.venue_id = venue_id
        order.items = json.loads(self.request.get('items'))
        order.customer = customer.key

        venue = iiko.Venue.venue_by_id(venue_id)
        company_id = venue.company_id
        token = iiko_api.get_access_token(company_id)

        return self.render_json({"promos": iiko_api.get_order_promos(order, token)})


class GetCompanyInfoHandler(BaseHandler):
    def get(self, company_id):
        company = Company.get_by_id(int(company_id))
        news = company.get_news()
        self.render_json({
            "news": news.dict() if news else None,
            "card_button_text": company.card_button_text or u"Добавить карту"
        })

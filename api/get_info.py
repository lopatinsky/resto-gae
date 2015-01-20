# coding=utf-8

from api.base import BaseHandler
from methods.maps import get_address_by_key
import json
from methods import iiko_api
from models import iiko
import datetime
import logging
from models.iiko import Company, ClientInfo


class GetAddressByKeyHandler(BaseHandler):

    """ /api/get_info """

    def get(self):
        key = self.request.get('key')

        info = get_address_by_key(key)

        return json.loads(self.render_json(info)).get()


class GetVenuePromosHandler(BaseHandler):

    def get(self):
        venue_id = self.request.get('venue_id')
        return self.render_json({"promos": iiko_api.get_venue_promos(venue_id)})


class GetOrderPromosHandler(BaseHandler):

    def get(self):
        venue_id = self.request.get('venue_id')
        name = self.request.get('name').strip()
        phone = self.request.get('phone')
        if len(phone) == 10 and not phone.startswith("7"):  # old Android version
            phone = "7" + phone
        customer_id = self.request.get('customer_id')
        order_sum = self.request.get('sum')
        items = json.loads(self.request.get('items'))
        date = self.request.get_range('date')

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
        order.date = datetime.datetime.fromtimestamp(date)
        order.venue_id = venue_id
        order.items = items
        order.customer = customer.key

        order_dict = iiko_api.prepare_order(order, customer, None)
        iiko_api.set_discounts(order, order_dict['order'])

        venue = iiko.Venue.venue_by_id(venue_id)
        company_id = venue.company_id

<<<<<<< HEAD
        return self.render_json({"promos": iiko_api.get_order_promos(order, token), "order": order_dict})
=======
        return self.render_json({"promos": iiko_api.get_order_promos(order)})
>>>>>>> origin/master


class GetCompanyInfoHandler(BaseHandler):
    def get(self, company_id):
        company = Company.get_by_id(int(company_id))
        news = company.get_news()
        self.render_json({
            "news": news.dict() if news else None,
            "card_button_text": company.card_button_text or u"Добавить карту",
            "card_button_subtext": company.card_button_subtext or "",
        })


class SaveClientInfoHandler(BaseHandler):
    def post(self, company_id):
        email = self.request.get("client_email")
        phone = self.request.get("client_phone")
        ClientInfo(company_id=int(company_id), email=email, phone=phone).put()
        self.render_json({})

# coding=utf-8

from api.base import BaseHandler
from methods.maps import get_address_by_key
import json
from methods import iiko_api, working_hours
from models import iiko
import datetime
from models.iiko import Company, ClientInfo, Venue
from config import config
import logging


class GetAddressByKeyHandler(BaseHandler):

    """ /api/get_info """

    def get(self):
        key = self.request.get('key')
        info = get_address_by_key(key)
        return json.loads(self.render_json(info)).get()


class GetVenuePromosHandler(BaseHandler):

    def get(self):
        venue_id = self.request.get('venue_id')
        phone = self.request.get('phone')
        company_id = Venue.venue_by_id(venue_id).company_id
        return self.render_json({
            "promos": iiko_api.get_venue_promos(venue_id),
            "balance": iiko_api.get_customer_by_phone(company_id, phone, venue_id).get('balance', 0.0)
        })


class GetOrderPromosHandler(BaseHandler):

    def post(self):
        venue_id = self.request.get('venue_id')
        venue = Venue.venue_by_id(venue_id)
        company = Company.get_by_id(venue.company_id)
        name = self.request.get('name').strip()
        phone = self.request.get('phone')
        if len(phone) == 10 and not phone.startswith("7"):  # old Android version
            phone = "7" + phone
        customer_id = self.request.get('customer_id')
        order_sum = self.request.get('sum')
        date = self.request.get_range('date')

        customer = iiko.Customer.customer_by_customer_id(customer_id) if customer_id else None
        if not customer:
            customer = iiko.Customer()
            customer.phone = phone
            customer.name = name
            if customer_id:
                customer.customer_id = customer_id

        order = iiko.Order()
        order.date = datetime.datetime.fromtimestamp(date)
        order.venue_id = venue_id
        order.sum = float(order_sum)
        order.items = json.loads(self.request.get('items'))

        order_dict = iiko_api.prepare_order(order, customer, None)

        local_time = order.date + datetime.timedelta(seconds=venue.get_timezone_offset())
        is_open = working_hours.is_datetime_valid(company.schedule, local_time) if company.schedule else True

        error = None
        for restriction in config.RESTRICTIONS:
            if venue_id in restriction['venues']:
                error = restriction['method'](order_dict, restriction['venues'][venue_id])
                logging.info(error)
                if error:
                    break

        if not company.is_iiko_system:
            return self.render_json({
                'is_open': is_open,
                'error': error
            })

        promos = iiko_api.get_order_promos(order, order_dict)
        iiko_api.set_discounts(order, order_dict['order'], promos)
        promos = iiko_api.get_order_promos(order, order_dict)

        max_bonus_payment = promos['maxPaymentSum']

        gifts = []
        if promos.get('availableFreeProducts'):
            for gift in promos['availableFreeProducts']:
                gifts.append({
                    'id': gift['id'],
                    'code': gift['code'],
                    'name': gift['name'],
                    'images': gift['images'],
                    'weight': gift['weight']
                })

        result = {
            #"promos": promos,
            #"order": order_dict,
            "order_discounts": order.discount_sum,
            "max_bonus_payment": max_bonus_payment if max_bonus_payment > 0 else 0,
            "gifts": gifts,
            "is_open": is_open,
            "error": error
        }
        logging.info(result)
        return self.render_json(result)


class GetCompanyInfoHandler(BaseHandler):
    def get(self, company_id):
        company = Company.get_by_id(int(company_id))
        news = company.get_news()
        self.render_json({
            "news": news.dict() if news else None,
            "card_button_text": company.card_button_text or u"Добавить карту",
            "card_button_subtext": company.card_button_subtext or "",
            'is_iiko': company.is_iiko_system
        })


class SaveClientInfoHandler(BaseHandler):
    def post(self, company_id):
        email = self.request.get("client_email")
        phone = self.request.get("client_phone")
        user_agent = self.request.headers['User-Agent']
        key = ClientInfo(company_id=int(company_id), email=email, phone=phone, user_agent=user_agent).put()
        self.render_json({'id': key.id()})

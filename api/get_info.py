# coding=utf-8

from api.base import BaseHandler
from methods.maps import get_address_by_key
import json
from methods import iiko_api, working_hours, filter_phone
from models import iiko
import datetime
from models.iiko import Company, ClientInfo, Venue
from config import config
import logging


CAT_FREE_CUP_CODE = '3308081521040820'
CUPS_BEFORE_FREE_CUP = 5


class GetAddressByKeyHandler(BaseHandler):

    """ /api/get_info """

    def get(self):
        key = self.request.get('key')
        info = get_address_by_key(key)
        return json.loads(self.render_json(info)).get()


class GetVenuePromosHandler(BaseHandler):

    def get(self):
        venue_id = self.request.get('venue_id')
        phone = filter_phone(self.request.get('phone'))
        company_id = Venue.venue_by_id(venue_id).company_id
        return self.render_json({
            "promos": iiko_api.get_venue_promos(venue_id),
            "balance": iiko_api.get_customer_by_phone(company_id, phone, venue_id).get('balance', 0.0)
        })


class GetOrderPromosHandler(BaseHandler):

    def send_error(self, description):
        self.render_json({
            'error': True,
            'description': description
        })

    def post(self):
        venue_id = self.request.get('venue_id')
        venue = Venue.venue_by_id(venue_id)
        company = Company.get_by_id(venue.company_id)
        name = self.request.get('name').strip()
        phone = filter_phone(self.request.get('phone'))
        customer_id = self.request.get('customer_id')
        order_sum = self.request.get('sum')
        date = self.request.get_range('date')
        logging.info(date)

        customer = iiko.Customer.customer_by_customer_id(customer_id) if customer_id else None
        if not customer:
            customer = iiko.Customer()
            if customer_id:
                customer.customer_id = customer_id
        customer.phone = phone
        customer.name = name

        order = iiko.Order()
        order.date = datetime.datetime.fromtimestamp(date)
        order.venue_id = venue_id
        order.sum = float(order_sum)
        order.items = json.loads(self.request.get('items'))

        order_dict = iiko_api.prepare_order(order, customer, None)

        local_time = order.date + datetime.timedelta(seconds=venue.get_timezone_offset())
        is_open = working_hours.is_datetime_valid(company.schedule, local_time) if company.schedule else True

        if not is_open:
            #if config.CHECK_SCHEDULE:  TODO: it is for get_promo endpoint, order should has check
            logging.info(company.schedule)
            start, end = working_hours.parse_company_schedule(company.schedule, local_time.isoweekday())
            if start < 10:
                start = '0%s' % start
            if end < 10:
                end = '0%s' % end
            return self.send_error(u'Заказы будут доступны c %s:00 до %s:00. Попробуйте в следующий раз.' % (start, end))

        error = None
        for restriction in config.RESTRICTIONS:
            if venue_id in restriction['venues']:
                error = restriction['method'](order_dict, restriction['venues'][venue_id])
                logging.info(error)
                if error:
                    break

        if error:
            return self.send_error(error)

        promos = iiko_api.get_order_promos(order, order_dict)
        iiko_api.set_discounts(order, order_dict['order'], promos)
        promos = iiko_api.get_order_promos(order, order_dict)

        discount_sum = order.discount_sum

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
        accumulated_gifts = None
        if venue_id == Venue.EMPATIKA:
            free_cup = iiko_api.get_product_from_menu(venue_id, product_code=CAT_FREE_CUP_CODE)
            FREE_CUP_IN_ORDER = 10
            CUPS_IN_ORDER = FREE_CUP_IN_ORDER * CUPS_BEFORE_FREE_CUP
            mock_order = order
            mock_order.sum = free_cup['price'] * CUPS_IN_ORDER
            mock_order.items = [{
                'id': free_cup['productId'],
                'name': free_cup['name'],
                'amount': CUPS_IN_ORDER
            }]
            mock_order_dict = iiko_api.prepare_order(mock_order, customer, None)
            mock_promos = iiko_api.get_order_promos(mock_order, mock_order_dict)
            iiko_api.set_discounts(mock_order, mock_order_dict['order'], mock_promos)
            logging.info(mock_promos)
            accumulated_gifts = mock_order.discount_sum / free_cup['price'] - FREE_CUP_IN_ORDER

        result = {
            "order_discounts": discount_sum,
            "max_bonus_payment": max_bonus_payment if max_bonus_payment > 0 else 0,
            "gifts": gifts,
            "error": False,
            "accumulated_gifts": accumulated_gifts
        }
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

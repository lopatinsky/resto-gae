# coding=utf-8
import copy
import json
import logging
import datetime
from config import config
from handlers.api.base import BaseHandler
from handlers.api.promos import CAT_FREE_CUP_CODES
from handlers.api.promos import CUPS_BEFORE_FREE_CUP
from methods.customer import get_resto_customer, update_customer_id, save_customer_info
from methods.iiko.customer import get_customer_by_id
from methods.iiko.menu import get_product_from_menu
from methods.iiko.order import prepare_order
from methods.iiko.promo import get_order_promos, set_discounts
from methods.rendering import filter_phone
from methods.specials.cat import fix_cat_items
from models import iiko
from models.iiko import DeliveryTerminal
from models.iiko import CompanyNew
from methods import working_hours

__author__ = 'dvpermyakov'


class CheckOrderHandler(BaseHandler):

    def send_error(self, description):
        self.render_json({
            'error': True,
            'description': description
        })

    def post(self):
        for k, v in self.request.POST.items():
            logging.debug("%s: %s", k, v)

        delivery_terminal_id = self.request.get('venue_id')
        delivery_terminal = DeliveryTerminal.get_by_id(delivery_terminal_id)
        if delivery_terminal:
            company = CompanyNew.get_by_id(delivery_terminal.company_id)
        else:
            company = CompanyNew.get_by_iiko_id(delivery_terminal_id)

        name = self.request.get('name').strip()
        phone = filter_phone(self.request.get('phone'))
        customer_id = self.request.get('customer_id')
        order_sum = self.request.get('sum')
        date = self.request.get_range('date')
        logging.info(date)

        customer = get_resto_customer(company, customer_id)
        save_customer_info(company, customer, name, self.request.headers, phone)
        update_customer_id(company, customer)

        items = json.loads(self.request.get('items'))
        if company.iiko_org_id == CompanyNew.COFFEE_CITY:
            fix_cat_items(items)

        order = iiko.Order()
        order.date = datetime.datetime.fromtimestamp(date)
        order.venue_id = company.iiko_org_id
        order.sum = float(order_sum)
        order.items = items

        order_dict = prepare_order(order, customer, None)

        local_time = order.date + datetime.timedelta(seconds=company.get_timezone_offset())
        is_open = working_hours.is_datetime_valid(company.schedule, local_time) if company.schedule else True

        if not is_open:
            logging.info(company.schedule)
            start, end = working_hours.parse_company_schedule(company.schedule, local_time.isoweekday())
            if start < 10:
                start = '0%s' % start
            if end < 10:
                end = '0%s' % end
            return self.send_error(u'Заказы будут доступны c %s:00 до %s:00. Попробуйте в следующий раз.' % (start, end))

        if company.is_iiko_system and order.items:
            promos = get_order_promos(order, order_dict)
            set_discounts(order, order_dict['order'], promos)
            promos = get_order_promos(order, order_dict)

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
            accumulated_gifts = 0
            if company.iiko_org_id in (CompanyNew.EMPATIKA, CompanyNew.COFFEE_CITY):
                free_codes = CAT_FREE_CUP_CODES[company.iiko_org_id]
                free_cup = get_product_from_menu(company.iiko_org_id, product_code=free_codes[0])
                FREE_CUP_IN_ORDER = 10
                CUPS_IN_ORDER = FREE_CUP_IN_ORDER * CUPS_BEFORE_FREE_CUP
                mock_order = copy.deepcopy(order)
                mock_order.sum = free_cup['price'] * CUPS_IN_ORDER
                mock_order.items = [{
                    'id': free_cup['productId'],
                    'name': free_cup['name'],
                    'amount': CUPS_IN_ORDER
                }]
                mock_order_dict = prepare_order(mock_order, customer, None)
                mock_promos = get_order_promos(mock_order, mock_order_dict)
                set_discounts(mock_order, mock_order_dict['order'], mock_promos)
                accumulated_gifts = int(mock_order.discount_sum / free_cup['price']) - FREE_CUP_IN_ORDER

            discount_gifts = 0
            if company.iiko_org_id in (CompanyNew.EMPATIKA, CompanyNew.COFFEE_CITY):
                for item in order.items:
                    free_codes = CAT_FREE_CUP_CODES[company.iiko_org_id]
                    if item['code'] in free_codes:
                        if item.get('discount_sum'):
                            price = (item['sum'] + item['discount_sum']) / item['amount']
                            discount_gifts += item['discount_sum'] / price
                    item['amount'] = int(item['amount'])
        else:
            discount_sum = 0.0
            max_bonus_payment = 0.0
            gifts = []
            accumulated_gifts = discount_gifts = 0

        iiko_customer = get_customer_by_id(company, customer.customer_id)

        result = {
            "order_discounts": discount_sum,
            "max_bonus_payment": max_bonus_payment if max_bonus_payment > 0 else 0,
            "gifts": gifts,
            "error": False,
            "accumulated_gifts": max(0, int(accumulated_gifts - discount_gifts)),
            "items": order.items,
            "balance": iiko_customer.get('balance', 0.0)
        }
        return self.render_json(result)
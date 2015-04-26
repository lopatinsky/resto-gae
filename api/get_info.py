# coding=utf-8
import copy

from api.base import BaseHandler
from api.specials import fix_modifiers_by_own
from api.specials import fix_syrop
from methods.maps import get_address_by_key
import json
from methods import iiko_api, working_hours, filter_phone
from models import iiko
import datetime
from models.iiko import CompanyNew, ClientInfo, DeliveryTerminal
from config import config
import logging


CAT_FREE_CUP_CODES = {
    CompanyNew.EMPATIKA: ['3308081521040829', '3308081521040830'],
    CompanyNew.COFFEE_CITY: ['0264', '0265', '0266', '0267', '0268', '0269', '0272'],
}
CUPS_BEFORE_FREE_CUP = 5


class GetAddressByKeyHandler(BaseHandler):

    """ /api/get_info """

    def get(self):
        key = self.request.get('key')
        info = get_address_by_key(key)
        return json.loads(self.render_json(info)).get()


def _do_get_promos(company, phone):
    branch = []
    if company.iiko_org_id in config.INVITATION_BRANCH_VENUES:
        branch.append({
            'info': 'Пригласи друга'
        })
    if company.iiko_org_id in config.GIFT_BRANCH_VENUES:
        branch.append({
            'info': 'Подари другу'
        })
    return {
        "branch": branch,
        "promos": iiko_api.get_venue_promos(company.iiko_org_id),
        "balance": iiko_api.get_customer_by_phone(company, phone).get('balance', 0.0)
    }


class CompanyPromosHandler(BaseHandler):
    def get(self, company_id):
        company = CompanyNew.get_by_id(int(company_id))
        phone = filter_phone(self.request.get('phone'))
        self.render_json(_do_get_promos(company, phone))


class GetVenuePromosHandler(BaseHandler):

    def get(self):
        delivery_terminal_id = self.request.get('venue_id')
        delivery_terminal = DeliveryTerminal.get_by_id(delivery_terminal_id)
        if delivery_terminal:
            org_id = delivery_terminal.iiko_organization_id
        else:
            org_id = delivery_terminal_id
        company = CompanyNew.get_by_iiko_id(org_id)
        phone = filter_phone(self.request.get('phone'))

        self.render_json(_do_get_promos(company, phone))


class GetOrderPromosHandler(BaseHandler):

    def send_error(self, description):
        self.render_json({
            'error': True,
            'description': description
        })

    def post(self):
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

        customer = iiko.Customer.customer_by_customer_id(customer_id) if customer_id else None
        if not customer:
            customer = iiko.Customer()
            if customer_id:
                customer.customer_id = customer_id
        customer.phone = phone
        customer.name = name

        items = json.loads(self.request.get('items'))
        if company.iiko_org_id == CompanyNew.COFFEE_CITY:
            items = fix_syrop.set_syrop_items(items)
            items = fix_modifiers_by_own.set_modifier_by_own(company.iiko_org_id, items)

        order = iiko.Order()
        order.date = datetime.datetime.fromtimestamp(date)
        order.venue_id = company.iiko_org_id
        order.sum = float(order_sum)
        order.items = items

        order_dict = iiko_api.prepare_order(order, customer, None)

        local_time = order.date + datetime.timedelta(seconds=company.get_timezone_offset())
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
            if company.iiko_org_id in restriction['venues']:
                error = restriction['method'](order_dict, restriction['venues'][company.iiko_org_id])
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
        accumulated_gifts = 0
        if company.iiko_org_id in (CompanyNew.EMPATIKA, CompanyNew.COFFEE_CITY):
            free_codes = CAT_FREE_CUP_CODES[company.iiko_org_id]
            free_cup = iiko_api.get_product_from_menu(company.iiko_org_id, product_code=free_codes[0])
            FREE_CUP_IN_ORDER = 10
            CUPS_IN_ORDER = FREE_CUP_IN_ORDER * CUPS_BEFORE_FREE_CUP
            mock_order = copy.deepcopy(order)
            mock_order.sum = free_cup['price'] * CUPS_IN_ORDER
            mock_order.items = [{
                'id': free_cup['productId'],
                'name': free_cup['name'],
                'amount': CUPS_IN_ORDER
            }]
            mock_order_dict = iiko_api.prepare_order(mock_order, customer, None)
            mock_promos = iiko_api.get_order_promos(mock_order, mock_order_dict)
            iiko_api.set_discounts(mock_order, mock_order_dict['order'], mock_promos)
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

        balance = iiko_api.get_customer_by_phone(company, phone).get('balance', 0.0)

        result = {
            "order_discounts": discount_sum,
            "max_bonus_payment": max_bonus_payment if max_bonus_payment > 0 else 0,
            "gifts": gifts,
            "error": False,
            "accumulated_gifts": max(0, int(accumulated_gifts - discount_gifts)),
            "items": order.items,
            "balance": balance
        }
        return self.render_json(result)


class GetCompanyInfoHandler(BaseHandler):
    def get(self, company_id):
        company = CompanyNew.get_by_id(int(company_id))
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

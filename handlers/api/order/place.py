# coding=utf-8
import json
import logging
import datetime
import random

from google.appengine.api.urlfetch_errors import DownloadError
from google.appengine.ext import deferred
from handlers.api.base import BaseHandler
from methods.customer import get_resto_customer, set_customer_info, update_customer_id

from methods.email.admin import send_error, send_order_email
from methods.alfa_bank import get_back_blocked_sum
from methods.iiko.menu import fix_modifier_amount
from methods.iiko.order import prepare_order, place_order
from methods.iiko.order import pre_check_order
from methods.iiko.promo import calc_sum
from methods.orders.create import pay_by_card
from methods.orders.precheck import set_discounts_bonuses_gifts
from methods.orders.validation import validate_order
from methods.rendering import parse_iiko_time, filter_phone, parse_str_date, prepare_address
from methods.sms import send_confirmation
from models import iiko
from models.iiko import CompanyNew, ClientInfo, DeliveryTerminal, PaymentType
from methods.specials.cat import fix_syrop, fix_modifiers_by_own
from models.iiko.order import AUTO_APP_SOURCE

__author__ = 'dvpermyakov'


GENERAL_ERROR = -1
MIN_SUM_ERROR = 0
NOT_VALID_TIME_ERROR = 1

_GIFT_COMMENT_TEMPLATE = u'Первый заказ, %s в подарок. '
_FIRST_ORDER_COMMENTS = {
    CompanyNew.OMNOMNOM: (_GIFT_COMMENT_TEMPLATE % u'Саке маки', ''),
    CompanyNew.TYKANO: (_GIFT_COMMENT_TEMPLATE % u'ролл Калифорния', ''),
    CompanyNew.ORANGE_EXPRESS: (u'Первый заказ из приложения. ', u'Повторный заказ из приложения. '),
}


class PlaceOrderHandler(BaseHandler):
    def send_error(self, description, error_code=GENERAL_ERROR):
        self.response.set_status(400)
        logging.warning(description)
        send_error("order", "Our pre check failed", description)
        self.render_json({
            'error': True,
            'error_code': error_code,
            'description': description
        })

    def post(self, delivery_terminal_id):
        logging.info(self.request.POST)

        custom_data = None
        try:
            custom_data = json.loads(self.request.get('custom_data'))
        except ValueError:
            pass

        bonus_sum = self.request.get('bonus_sum')
        bonus_sum = float(bonus_sum) if bonus_sum else 0.0
        discount_sum = self.request.get('discount_sum')
        discount_sum = float(discount_sum) if discount_sum else 0.0
        customer_id = self.request.get('customer_id') or self.request.get('customerId')
        address = self.request.get('address')
        comment = self.request.get('comment')
        binding_id = self.request.get('binding_id')
        alpha_client_id = self.request.get('alpha_client_id')
        source = self.request.get('source')

        delivery_terminal = DeliveryTerminal.get_by_id(delivery_terminal_id)
        if delivery_terminal:
            org_id = delivery_terminal.iiko_organization_id
        else:
            org_id = delivery_terminal_id

        company = CompanyNew.get_by_iiko_id(org_id)
        if not delivery_terminal:
            delivery_terminal = DeliveryTerminal.get_any(company.iiko_org_id)
            delivery_terminal_id = delivery_terminal.key.id()
        response_delivery_terminal_id = delivery_terminal_id

        customer = get_resto_customer(company, customer_id)
        set_customer_info(company, customer,
                          self.request.get('name').strip(),
                          self.request.headers,
                          filter_phone(self.request.get('phone')),
                          custom_data)
        update_customer_id(company, customer)

        order = iiko.Order()
        if source == AUTO_APP_SOURCE:
            order.source = source
        order.date = datetime.datetime.utcfromtimestamp(int(self.request.get('date')))
        order.payment_type = self.request.get('paymentType')

        str_date = self.request.get('str_date')
        if str_date:
            parsed_str_date = parse_str_date(str_date)
            if parsed_str_date:
                order.date = parsed_str_date - datetime.timedelta(seconds=company.get_timezone_offset())
            else:
                logging.warning("Failed to parse str_date: %s", str_date)
                order.date = datetime.datetime.now() + datetime.timedelta(hours=1)

        if order.date < datetime.datetime.utcnow() and \
                ('/2.0 ' in self.request.user_agent or '/2.0.1' in self.request.user_agent):
            logging.info('new date(str): %s' % order.date)
            order.date += datetime.timedelta(hours=12)
            logging.info("ios v2.0 fuckup, adding 12h: %s", order.date)

        send_confirmation_sms = False
        if company.iiko_org_id in (CompanyNew.EMPATIKA, CompanyNew.ORANGE_EXPRESS):
            confirm_by_phone = self.request.get("confirm_by_phone")
            if confirm_by_phone == "1":
                comment = u"Клиент просит перезвонить. " + comment
            elif confirm_by_phone == "0":
                comment = u"Клиенту будет отправлено СМС-подтверждение. " + comment
                send_confirmation_sms = True
            else:
                pass  # old version

        order.delivery_terminal_id = delivery_terminal_id
        order.venue_id = company.iiko_org_id
        gifts = json.loads(self.request.get('gifts')) if self.request.get('gifts') else []
        order.customer = customer.key

        items = fix_modifier_amount(company.iiko_org_id, json.loads(self.request.get('items')))

        if company.iiko_org_id == CompanyNew.COFFEE_CITY:
            items = fix_syrop.set_syrop_items(items)
            items = fix_modifiers_by_own.set_modifier_by_own(items)

        order.items = items
        order.initial_sum = order.sum = calc_sum(items, company.iiko_org_id)
        logging.info("calculated sum: %s, app sum: %s", order.sum, self.request.get('sum'))

        if company.iiko_org_id == CompanyNew.DIMASH:
            if 'Android' in self.request.user_agent:
                comment = u"Заказ с Android. " + comment
            else:
                comment = u"Заказ с iOS. " + comment
        if company.iiko_org_id in _FIRST_ORDER_COMMENTS:
            comment_first, comment_repeated = _FIRST_ORDER_COMMENTS[company.iiko_org_id]
            customers = iiko.Customer.query(iiko.Customer.phone == customer.phone).fetch(keys_only=True)
            orders = [o
                      for lst in [iiko.Order.query(iiko.Order.customer == c,
                                                   iiko.Order.status.IN((iiko.Order.NOT_APPROVED,
                                                                         iiko.Order.APPROVED,
                                                                         iiko.Order.CLOSED))
                                                   ) for c in customers]
                      for o in lst]
            comment = (comment_repeated if orders else comment_first) + comment

        order.comment = comment
        delivery_type = self.request.get_range('deliveryType')
        order.is_delivery = (delivery_type == 0)
        if order.is_delivery:
            if not address:
                self.abort(400)
            try:
                order.address = json.loads(address)
                success = prepare_address(order)
                if not success:
                    send_error("address", "Address is not valid", order.address['comment'])
            except Exception as e:
                logging.exception(e)
                self.abort(400)
        order.delivery_type = None
        for company_delivery_type in company.delivery_types:
            company_delivery_type = company_delivery_type.get()
            if company_delivery_type.delivery_id == delivery_type:
                order.delivery_type = company_delivery_type

        validation_result = validate_order(company, delivery_terminal, order, customer)
        if not validation_result['valid']:
            return self.send_error(validation_result['errors'][0])

        # this resets order.delivery_terminal_id if it is delivery (not takeout)
        order_dict = prepare_order(order, customer, order.payment_type)
        pre_check_result = pre_check_order(company, order_dict)
        if 'code' in pre_check_result:
            logging.warning('iiko pre check failed')
            msg = pre_check_result["description"] or pre_check_result["message"]
            send_error("iiko", "iiko pre check failed", msg)
            self.abort(400)

        order.discount_sum = 0.0
        order.bonus_sum = 0.0
        if company.is_iiko_system:
            success = set_discounts_bonuses_gifts(order, order_dict, discount_sum, bonus_sum, gifts)
            if not success:
                self.abort(409)
            order.sum -= order.bonus_sum + order.discount_sum

        # pay after pre check
        order_id = None
        if order.payment_type == PaymentType.CARD:
            success, order_id = pay_by_card(company, order, order_dict, binding_id, alpha_client_id)
            if not success:
                self.abort(400)
        order.alfa_order_id = order_id

        result = place_order(company, order_dict)

        if 'code' in result.keys():
            logging.error('iiko failure')
            if order.payment_type == PaymentType.CARD:
                # return money
                return_result = get_back_blocked_sum(company, order_id)
                logging.info('return')
                logging.info(return_result)
            msg = result["description"] or result["message"]
            send_error("iiko", "iiko place order failed", msg)
            self.response.set_status(400)
            return self.render_json(result)

        customer.customer_id = result['customerId']
        customer.put()
        order.customer = customer.key

        client_info_id = self.request.get_range('user_data_id')
        if client_info_id:
            client_info = ClientInfo.get_by_id(client_info_id)
            if client_info and client_info.customer != customer.key:
                client_info.customer = customer.key
                client_info.put()

        order.order_id = result['orderId']
        order.number = result['number']
        order.set_status(result['status'])
        order.created_in_iiko = parse_iiko_time(result['createdTime'], company)

        order.put()

        try:
            send_order_email(order, customer, company)
        except DownloadError:
            logging.warning('mandrill is not responsed')

        if send_confirmation_sms:
            countdown = random.randint(120, 420)  # make it realistic
            deferred.defer(send_confirmation, order.key, _countdown=countdown)

        response_items = order.items
        if company.iiko_org_id == CompanyNew.COFFEE_CITY:
            response_items = json.loads(json.dumps(order.items))
            for item in response_items:
                fix_modifiers_by_own.remove_modifiers_from_item(item)

        resp = {
            'customer_id': customer.customer_id,
            'order': {
                'order_id': order.order_id,
                'resto_id': order.key.id(),
                'status': order.status,
                'items': response_items,
                'sum': order.sum,
                'payments': order_dict['order']['paymentItems'],  # it was added
                'number': order.number,
                'venue_id': response_delivery_terminal_id,
                'address': order.address,
                'date': int(self.request.get('date')),
                },
            'error': False,
            'error_code': 0,
        }
        logging.info(resp)

        self.render_json(resp)
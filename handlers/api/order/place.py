# coding=utf-8
import json
import logging
import datetime
import time
import re

from google.appengine.api.urlfetch_errors import DownloadError
from handlers.api.base import BaseHandler

from methods.email.admin import send_error, send_order_email
from methods.alfa_bank import tie_card, create_pay, get_back_blocked_sum, check_extended_status, get_bindings
from methods.iiko.order import prepare_order, place_order
from methods.iiko.order import pre_check_order
from methods.iiko.promo import calc_sum, get_order_promos, set_gifts, add_bonus_to_payment, set_discounts
from methods.rendering import parse_iiko_time, filter_phone
from models import iiko
from models.iiko import CompanyNew, ClientInfo, DeliveryTerminal, BonusCardHack
from methods.specials.cat import fix_syrop, fix_modifiers_by_own
from methods.orders.validation import check_stop_list, check_company_schedule, check_config_restrictions


__author__ = 'dvpermyakov'


GENERAL_ERROR = -1
MIN_SUM_ERROR = 0
NOT_VALID_TIME_ERROR = 1


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
        name = self.request.get('name').strip()
        phone = filter_phone(self.request.get('phone'), check=True)
        if not phone:
            return self.send_error(u"Номер телефона имеет неверный формат. ")
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
        delivery_type = self.request.get('deliveryType', 0)
        payment_type = self.request.get('paymentType')
        address = self.request.get('address')
        comment = self.request.get('comment')
        binding_id = self.request.get('binding_id')
        alpha_client_id = self.request.get('alpha_client_id')

        phone, bonus_card_customer_id = BonusCardHack.check(phone)

        customer = iiko.Customer.customer_by_customer_id(customer_id)
        if not customer:
            customer = iiko.Customer()
            if customer_id:
                customer.customer_id = customer_id
        if not customer.user_agent:
            customer.user_agent = self.request.headers['User-Agent']
        customer.phone = phone
        customer.name = name
        customer.custom_data = custom_data

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

        order = iiko.Order()
        order.date = datetime.datetime.utcfromtimestamp(int(self.request.get('date')))

        if self.request.get('str_date'):
            str_date = self.request.get('str_date')
            try:
                try:
                    order.date = datetime.datetime.strptime(str_date, '%Y-%m-%d %H:%M:%S')
                except ValueError:
                    order.date = datetime.datetime.strptime(str_date, '%Y-%m-%d %H:%M:%S %p')
            except ValueError:
                pass
            else:
                order.date -= datetime.timedelta(seconds=company.get_timezone_offset())
                logging.info('new date(str): %s' % order.date)
                if order.date < datetime.datetime.now() and \
                        ('/2.0 ' in self.request.user_agent or '/2.0.1' in self.request.user_agent):
                    order.date += datetime.timedelta(hours=12)
                    logging.info("ios v2.0 fuckup, adding 12h: %s", order.date)

        if order.date < datetime.datetime.now():
            return self.send_error(u"Вы выбрали некорректное время доставки. "
                                   u"Пожалуйста, выберите время, большее текущего времени.")

        pt = company.get_payment_type(payment_type)
        if not pt or not pt.available:
            return self.send_error(u"Выбранный способ оплаты недоступен.")

        success, description = check_company_schedule(company, order)
        if not success:
            return self.send_error(description, error_code=NOT_VALID_TIME_ERROR)

        order.delivery_terminal_id = delivery_terminal_id
        order.venue_id = company.iiko_org_id
        gifts = json.loads(self.request.get('gifts')) if self.request.get('gifts') else []
        order.customer = customer.key

        items = json.loads(self.request.get('items'))
        for item in items:
            if "modifiers" in item:
                for mod in item["modifiers"]:
                    if mod["amount"] == 0 and mod.get("groupId"):
                        mod["amount"] = 1
                item["modifiers"] = [mod for mod in item["modifiers"] if mod["amount"]]
        if company.iiko_org_id == CompanyNew.COFFEE_CITY:
            items = fix_syrop.set_syrop_items(items)
            items = fix_modifiers_by_own.set_modifier_by_own(company.iiko_org_id, items)
        order.items = items
        order.sum = calc_sum(items, company.iiko_org_id)
        logging.info("calculated sum: %s, app sum: %s", order.sum, self.request.get('sum'))
        if company.min_order_sum and order.sum < company.min_order_sum:
            return self.send_error(u"Минимальная сумма заказа %s рублей!" % company.min_order_sum)

        if company.iiko_org_id == CompanyNew.DIMASH:
            if 'Android' in self.request.user_agent:
                comment = u"Заказ с Android. " + comment
            else:
                comment = u"Заказ с iOS. " + comment
        order.comment = comment
        order.is_delivery = int(delivery_type) == 0
        order.payment_type = payment_type
        if order.is_delivery:
            if not address:
                self.abort(400)
            try:
                order.address = json.loads(address)
                if not order.address["home"].strip():
                    return self.send_error(u"Не введен номер дома. Пожалуйста, введите его и попробуйте еще раз.")
            except Exception as e:
                logging.exception(e)
                self.abort(400)

        # this resets order.delivery_terminal_id if it is delivery (not takeout)
        order_dict = prepare_order(order, customer, payment_type)
        pre_check_result = pre_check_order(company, order_dict)
        if 'code' in pre_check_result:
            logging.warning('iiko pre check failed')
            send_error("iiko", "iiko pre check failed", pre_check_result["description"])
            self.abort(400)

        success, description = check_config_restrictions(company, order_dict)
        if not success:
            return self.send_error(description)

        order.discount_sum = 0.0
        order.bonus_sum = 0.0
        if company.is_iiko_system:
            promos = get_order_promos(order, order_dict)
            logging.info('discount %s' % discount_sum)
            logging.info('bonus %s' % bonus_sum)
            logging.info('gifts %s' % gifts)
            if discount_sum != 0:
                set_discounts(order, order_dict['order'], promos)
                if order.discount_sum != discount_sum:
                    logging.info('conflict_discount: app(%s), iiko(%s)' % (discount_sum, order.discount_sum))
                    self.abort(409)
                promos = get_order_promos(order, order_dict)
            if bonus_sum != 0:
                if bonus_sum != promos['maxPaymentSum']:
                    logging.info('conflict_max_bonus: app(%s), iiko(%s)' % (bonus_sum, promos['maxPaymentSum']))
                    self.abort(409)
                add_bonus_to_payment(order_dict['order'], bonus_sum, True)
                order.bonus_sum = bonus_sum

            if gifts:
                if not promos.get('availableFreeProducts'):
                    logging.info('conflict_gift: app(%s), iiko(%s)' % (gifts, None))
                    self.abort(409)

                def get_iiko_item(items, cur_item):
                    for item in items:
                        if item['id'] == cur_item['id']:
                            return item
                    return None

                iiko_gifts = []
                for gift in gifts:
                    iiko_gift = get_iiko_item(promos.get('availableFreeProducts'), gift)
                    if not iiko_gift:
                        logging.info('conflict_gift: app(%s), iiko(%s)' % (gift, None))
                        self.abort(409)
                    else:
                        iiko_gift['amount'] = gift.get('amount', 1)
                        iiko_gifts.append(iiko_gift)

                set_gifts(order, order_dict['order'], iiko_gifts)
        order.sum -= order.bonus_sum + order.discount_sum

        # todo: set here validation stop-list
        success, description = check_stop_list(items, delivery_terminal)
        if not success:
            return self.send_error(description)

        # pay after pre check
        order_id = None
        if payment_type == '2':
            # todo android binding_id fuckup
            if not re.match('\w{8}-\w{4}-\w{4}-\w{4}-\w{12}$', binding_id):
                logging.info('wrong binding_id: %s', binding_id)
                pan = binding_id[-4:]
                bindings = get_bindings(company, alpha_client_id)
                logging.info('got bindings from alfa: %s', bindings)
                for binding in bindings['bindings']:
                    if binding['maskedPan'][-4:] == pan:
                        logging.info('found binding: %s', bindings)
                        binding_id = binding['bindingId']
                        break
                else:
                    logging.warning('binding not found')

            tie_result = tie_card(company, int(order.sum * 100), int(time.time()), 'returnUrl', alpha_client_id,
                                  'MOBILE')
            logging.info("registration")
            logging.info(str(tie_result))
            if 'errorCode' not in tie_result.keys() or str(tie_result['errorCode']) == '0':
                order_id = tie_result['orderId']
                create_result = create_pay(company, binding_id, order_id)
                logging.info("block")
                logging.info(str(create_result))
                if 'errorCode' not in create_result.keys() or str(create_result['errorCode']) == '0':
                    status_check_result = check_extended_status(company, order_id)['alfa_response']
                    logging.info("status check")
                    logging.info(str(status_check_result))
                    if str(status_check_result.get('errorCode')) == '0' and \
                            status_check_result['actionCode'] == 0 and status_check_result['orderStatus'] == 1:
                        # payment succeeded
                        order.comment += u"\nЗаказ оплачен картой через приложение"
                        order_dict["order"]["comment"] = order.comment
                    else:
                        self.abort(400)
                else:
                    self.abort(400)
            else:
                self.abort(400)
        order.alfa_order_id = order_id

        result = place_order(company, order_dict)

        if 'code' in result.keys():
            logging.error('iiko failure')
            if payment_type == '2':
                # return money
                return_result = get_back_blocked_sum(company, order_id)
                logging.info('return')
                logging.info(return_result)
            send_error("iiko", "iiko place order failed", result["description"])
            self.response.set_status(400)
            return self.render_json(result)
        if not customer_id:
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

        response_items = order.items
        if company.iiko_org_id == CompanyNew.COFFEE_CITY:
            response_items = json.loads(json.dumps(order.items))
            for item in response_items:
                fix_modifiers_by_own.remove_modifiers_from_item(item)

        resp = {
            'customer_id': customer.customer_id,
            #'success': True,
            #'promos': promos,  # it was added
            #'menu': iiko_api.list_menu(venue_id),  # it was added
            'order': {
                'order_id': order.order_id,
                'status': order.status,
                'items': response_items,
                'sum': order.sum,
                #'discounts': order.discount_sum,  # it was added
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
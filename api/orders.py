# coding=utf-8
import json
import logging
import datetime
import time
import re
from google.appengine.api.urlfetch_errors import DownloadError
from api.specials.express_emails import send_express_email
from api.specials.mivako_promo import MIVAKO_NY2015_ENABLED
import base
from methods import email, iiko_api, filter_phone
from methods.alfa_bank import tie_card, create_pay, get_back_blocked_sum, check_extended_status, get_bindings
from models import iiko
from models.iiko import CompanyNew, ClientInfo, Order, DeliveryTerminal
from models.specials import MivakoGift
from specials import fix_syrop, fix_modifiers_by_own
from methods.orders.validation import check_stop_list, check_company_schedule, check_config_restrictions


class PlaceOrderHandler(base.BaseHandler):
    """ /api/venue/%s/order/new """

    def send_error(self, description):
        self.response.set_status(400)
        logging.warning(description)
        self.render_json({
            'error': True,
            'description': description
        })

    def post(self, delivery_terminal_id):
        logging.info(self.request.POST)
        name = self.request.get('name').strip()
        phone = filter_phone(self.request.get('phone'))
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

        # TODO: ios 7 times fuckup
        if self.request.get('str_date'):
            order.date = datetime.datetime.strptime(self.request.get('str_date'), '%Y-%m-%d %H:%M:%S')
            order.date -= datetime.timedelta(seconds=company.get_timezone_offset())
            logging.info('new date(str): %s' % order.date)
        elif 'iOS 7' in self.request.headers['User-Agent']:
            order.date += datetime.timedelta(hours=1)
            logging.info('new date(ios 7): %s' % order.date)
        # TODO: ios 7 times fuckup

        pt = company.get_payment_type(payment_type)
        if not pt or not pt.available:
            self.send_error(u"Выбранный способ оплаты недоступен.")

        success, description = check_company_schedule(company, order)
        if not success:
            self.send_error(description)

        order.delivery_terminal_id = delivery_terminal_id
        order.venue_id = company.iiko_org_id
        gifts = json.loads(self.request.get('gifts')) if self.request.get('gifts') else []
        order.customer = customer.key

        items = json.loads(self.request.get('items'))
        for item in items:
            if "modifiers" in item:
                for mod in item["modifiers"]:
                    if mod["amount"] == 0:
                        mod["amount"] = 1
        if company.iiko_org_id == CompanyNew.COFFEE_CITY:
            items = fix_syrop.set_syrop_items(items)
            items = fix_modifiers_by_own.set_modifier_by_own(company.iiko_org_id, items)
        order.items = items
        order.sum = iiko_api.calc_sum(items, company.iiko_org_id)
        logging.info("calculated sum: %s, app sum: %s", order.sum, self.request.get('sum'))

        order.comment = comment
        order.is_delivery = int(delivery_type) == 0
        order.payment_type = payment_type
        if order.is_delivery:
            if not address:
                self.abort(400)
            try:
                order.address = json.loads(address)
            except:
                self.abort(400)

        # this resets order.delivery_terminal_id if it is delivery (not takeout)
        order_dict = iiko_api.prepare_order(order, customer, payment_type)
        pre_check_result = iiko_api.pre_check_order(company, order_dict)
        if 'code' in pre_check_result:
            logging.warning('iiko pre check failed')
            email.send_error("iiko", "iiko pre check failed", pre_check_result["description"])
            self.abort(400)

        success, description = check_config_restrictions(company, order_dict)
        if not success:
            return self.send_error(description)

        order.discount_sum = 0.0
        order.bonus_sum = 0.0
        promos = None
        if company.is_iiko_system:
            promos = iiko_api.get_order_promos(order, order_dict)
            logging.info('discount %s' % discount_sum)
            logging.info('bonus %s' % bonus_sum)
            logging.info('gifts %s' % gifts)
            if discount_sum != 0:
                iiko_api.set_discounts(order, order_dict['order'], promos)
                if order.discount_sum != discount_sum:
                    logging.info('conflict_discount: app(%s), iiko(%s)' % (discount_sum, order.discount_sum))
                    self.abort(409)
                promos = iiko_api.get_order_promos(order, order_dict)
            if bonus_sum != 0:
                if bonus_sum != promos['maxPaymentSum']:
                    logging.info('conflict_max_bonus: app(%s), iiko(%s)' % (bonus_sum, promos['maxPaymentSum']))
                    self.abort(409)
                iiko_api.add_bonus_to_payment(order_dict['order'], bonus_sum, True)
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

                iiko_api.set_gifts(order, order_dict['order'], iiko_gifts)

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

            payment = order.sum - order.discount_sum - order.bonus_sum
            tie_result = tie_card(company, int(float(payment) * 100), int(time.time()), 'returnUrl', alpha_client_id,
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
                        if MIVAKO_NY2015_ENABLED and company.name == "empatikaMivako" and \
                                status_check_result["cardAuthInfo"]["pan"][0:2] in ("51", "52", "53", "54", "55"):
                            logging.info("Mivako NewYear2015 promo")
                            order.comment += u"\nОплата MasterCard через приложение: ролл Дракон в подарок"
                            order_dict["order"]["comment"] = order.comment
                            MivakoGift(
                                sender="MasterCard",
                                recipient=customer.phone,
                                recipient_name=customer.name,
                                gift_item=u"Ролл Дракон (оплата MasterCard через приложение)"
                            ).put()
                    else:
                        self.abort(400)
                else:
                    self.abort(400)
            else:
                self.abort(400)
        order.alfa_order_id = order_id

        result = iiko_api.place_order(company, order_dict)

        if 'code' in result.keys():
            logging.error('iiko failure')
            if payment_type == '2':
                # return money
                return_result = get_back_blocked_sum(company, order_id)
                logging.info('return')
                logging.info(return_result)
            email.send_error("iiko", "iiko place order failed", result["description"])
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
        order.created_in_iiko = iiko_api.parse_iiko_time(result['createdTime'], company)

        order.put()

        if company.iiko_org_id == CompanyNew.ORANGE_EXPRESS:
            try:
                send_express_email(order, customer, company)
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


class OrderInfoRequestHandler(base.BaseHandler):
    """ /api/order/%s """
    def get(self, order_id):
        order = iiko.Order.order_by_id(order_id)
        order.reload()

        self.render_json({
            'order': order.to_dict()
        })


class OrderRequestCancelHandler(base.BaseHandler):
    def post(self, order_id):
        order = Order.order_by_id(order_id)
        if order.status in (Order.NOT_APPROVED, Order.APPROVED):
            order.cancel_requested = True
            order.put()
            self.render_json({})
        else:
            self.response.set_status(400)
            self.render_json({'error': u"Заказ уже выдан или отменен"})

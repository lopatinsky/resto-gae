# coding=utf-8
import json
import logging
import datetime
import time
from api.specials.mivako_promo import MIVAKO_NY2015_ENABLED
import base
from methods import iiko_api
from methods.alfa_bank import tie_card, create_pay, get_back_blocked_sum, check_extended_status
from models import iiko
from models.iiko import Venue, Company
from models.specials import MivakoGift


class PlaceOrderHandler(base.BaseHandler):
    """ /api/venue/%s/order/new """

    def post(self, venue_id):
        logging.info(self.request.POST)

        name = self.request.get('name').strip()
        phone = self.request.get('phone')
        bonus_sum = self.request.get('bonus_sum')  # it was added
        bonus_sum = float(bonus_sum) if bonus_sum else 0.0
        discount_sum = self.request.get('discount_sum')  # it was added
        discount_sum = float(discount_sum) if discount_sum else 0.0
        if len(phone) == 10 and not phone.startswith("7"):  # old Android version
            phone = "7" + phone
        customer_id = self.request.get('customer_id')
        delivery_type = self.request.get('deliveryType', 0)
        payment_type = self.request.get('paymentType')
        address = self.request.get('address')
        comment = self.request.get('comment')
        order_sum = self.request.get('sum')
        binding_id = self.request.get('binding_id')
        alpha_client_id = self.request.get('alpha_client_id')

        customer = iiko.Customer.customer_by_customer_id(customer_id)
        if not customer:
            customer = iiko.Customer()
            customer.phone = phone
            customer.name = name
            if customer_id:
                customer.customer_id = customer_id
            customer.put()

        venue = Venue.venue_by_id(venue_id)
        company = Company.get_by_id(venue.company_id)
        company_id = company.key.id()

        order = iiko.Order()
        order.sum = float(order_sum)
        order.date = datetime.datetime.fromtimestamp(int(self.request.get('date')))
        order.venue_id = venue_id
        order.items = json.loads(self.request.get('items'))
        gifts = json.loads(self.request.get('gifts')) if self.request.get('gifts') else []
        order.customer = customer.key
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

        order_dict = iiko_api.prepare_order(order, customer, payment_type)
        pre_check_result = iiko_api.pre_check_order(company_id, order_dict)
        if 'code' in pre_check_result:
            logging.warning('iiko pre check failed')
            self.abort(400)

        order.discount_sum = 0.0
        order.bonus_sum = 0.0
        promos = None
        if company.is_iiko_system:
            promos = iiko_api.get_order_promos(order, order_dict)
            logging.info('discount %s' % discount_sum)
            logging.info('bonus %s' % bonus_sum)
            logging.info('gifts %s' % gifts)
            if discount_sum != 0:
                iiko_api.set_discounts(order, order_dict['order'], promos)  # it was added
                if order.discount_sum != discount_sum:
                    logging.info('conflict_discount: app(%s), iiko(%s)' % (discount_sum, order.discount_sum))
                    self.abort(409)
                promos = iiko_api.get_order_promos(order, order_dict)
            if bonus_sum != 0:
                if bonus_sum != promos['maxPaymentSum']:
                    logging.info('conflict_max_bonus: app(%s), iiko(%s)' % (bonus_sum, promos['maxPaymentSum']))
                    self.abort(409)
                iiko_api.add_bonus_to_payment(order_dict['order'], bonus_sum, True)  # it was added
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
                        iiko_gifts.append(iiko_gift)

                iiko_api.set_gifts(order, order_dict['order'], iiko_gifts)

        # pay after pre check
        order_id = None
        if payment_type == '2':
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

        result = iiko_api.place_order(company_id, order_dict)

        if 'code' in result.keys():
            logging.error('iiko failure')
            if payment_type == '2':
                # return money
                return_result = get_back_blocked_sum(company, order_id)
                logging.info('return')
                logging.info(return_result)
            self.response.set_status(500)
            return self.render_json(result)
        if not customer_id:
            customer.customer_id = result['customerId']
            customer.put()

        order.order_id = result['orderId']
        order.number = result['number']
        order.set_status(result['status'])

        order.put()

        resp = {
            'customer_id': customer.customer_id,
            #'promos': promos,  # it was added
            #'menu': iiko_api.list_menu(venue_id),  # it was added
            'order': {
                'order_id': order.order_id,
                'status': order.status,
                'items': order.items,
                'sum': order.sum,
                #'discounts': order.discount_sum,  # it was added
                'payments': order_dict['order']['paymentItems'],  # it was added
                'number': order.number,
                'venue_id': order.venue_id,
                'address': order.address,
                'date': int(self.request.get('date')),
                },
            'error_code': 0,
        }

        self.render_json(resp)


class VenueOrderInfoRequestHandler(base.BaseHandler):
    """ /api/venue/%s/order/%s """
    def get(self, venue_id, order_id):
        result = iiko_api.order_info1(order_id, venue_id)
        result['status'] = result['status'].replace(u'Новая', u'Подтвержден')
        result['status'] = result['status'].replace(u'Закрыта', u'Закрыт')

        self.render_json({
            'order': result
        })


class OrderInfoRequestHandler(base.BaseHandler):
    """ /api/order/%s """
    def get(self, order_id):
        order = iiko.Order.order_by_id(order_id)

        result = iiko_api.order_info(order)
        order.set_status(result['status'])
        order.put()

        self.render_json({
            'order': order.to_dict()
        })


class VenueNewOrderListHandler(base.BaseHandler):
    """ /api/venue/%s/new_orders """
    def get(self, venue_id):
        start = self.request.get_range("start")
        end = self.request.get_range("end")
        start_date = datetime.datetime.fromtimestamp(start) if start else None
        end_date = datetime.datetime.fromtimestamp(end) if end else None
        orders = iiko_api.get_new_orders(venue_id, start_date, end_date)
        logging.info(orders)

        menu = iiko_api.get_menu(venue_id)
        images_map = {}

        def process_category(category):
            for product in category['products']:
                images_map[product['productId']] = product['images']
            for subcategory in category['children']:
                process_category(subcategory)
        for c in menu:
            process_category(c)

        order_list = []
        for order in orders['deliveryOrders']:
            order_items = []
            for item in order['items']:
                order_items.append({
                    'sum': item['sum'],
                    'amount': item['amount'],
                    'name': item['name'],
                    'modifiers': item['modifiers'],
                    'id': item['id'],
                    'images': images_map.get(item['id'], [])
                })

            address = {}
            if order['address']:
                address = {'city': order['address']['city'],
                           'street': order['address']['street'],
                           'home': order['address']['home'],
                           'apartment': order['address']['apartment'],
                           'housing': order['address']['housing'],
                           'entrance': order['address']['entrance'],
                           'floor': order['address']['floor'], }

            order_list.append({
                'order_id': order['orderId'],
                'number': order['number'],
                'address': address,
                'createdDate': time.mktime(datetime.datetime.strptime(order['createdTime'], "%Y-%m-%d %H:%M:%S").timetuple()),
                'deliveryDate': time.mktime(datetime.datetime.strptime(order['deliveryDate'], "%Y-%m-%d %H:%M:%S").timetuple()),
                'client_id': order['customer']['id'],
                'phone': order['customer']['phone'],
                'discount': order['discount'],
                'sum': order['sum'],
                'items': order_items,
                'venue_id': venue_id,
                'status': iiko.Order.parse_status(order['status'])
            })
        logging.info(len(order_list))
        self.render_json({'orders': order_list})

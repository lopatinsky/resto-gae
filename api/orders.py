# coding=utf-8
import json
import logging
import datetime
import time
from api.specials.express_emails import send_express_email
from api.specials.mivako_promo import MIVAKO_NY2015_ENABLED
import base
from methods import iiko_api
from methods.alfa_bank import tie_card, create_pay, get_back_blocked_sum, check_extended_status
from models import iiko
from models.iiko import Venue, Company, ClientInfo
from models.specials import MivakoGift
from specials import fix_syrop, fix_modifiers_by_own


class PlaceOrderHandler(base.BaseHandler):
    """ /api/venue/%s/order/new """

    @classmethod
    def _do_promos(cls, company_id, order):
        return  # TODO enable
        
        # TODO: set discounts

        def get_item(product_id):
            for item in order.items:
                if item['id'] == product_id:
                    return item

        token = iiko_api.get_access_token(company_id)
        promos = iiko_api.get_order_promos(order)
        if promos.get('availableFreeProducts'):
            for gift in promos.get('availableFreeProducts'):
                gift['sum'] = 0
                order.items.append(gift)
        discount_sum = 0
        if promos.get('discountInfo'):
            for dis_info in promos.get('discountInfo'):
                if dis_info.get('details'):
                    for detail in dis_info.get('details'):
                        if detail.get('discountSum'):
                            item = get_item(detail.get('id'))
                            if not item.get('discount_sum'):
                                item['discount_sum'] = detail['discountSum']
                                discount_sum += item['discount_sum']
                            else:
                                pass  # TODO think about it
        order.discount_sum = discount_sum
        # TODO: end set discounts

    def post(self, venue_id):
        logging.info(self.request.POST)
        name = self.request.get('name').strip()
        phone = self.request.get('phone')
        if len(phone) == 10 and not phone.startswith("7"):  # old Android version
            phone = "7" + phone
        customer_id = self.request.get('customer_id') or self.request.get('customerId')
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
            if customer_id:
                customer.customer_id = customer_id
        customer.phone = phone
        customer.name = name

        venue = Venue.venue_by_id(venue_id)
        company = Company.get_by_id(venue.company_id)
        company_id = company.key.id()

        order = iiko.Order()
        order.sum = float(order_sum)
        #order.date = datetime.datetime.fromtimestamp(int(self.request.get('date')))
        order.date = datetime.datetime.utcfromtimestamp(int(self.request.get('date')))
        order.venue_id = venue_id

        items = json.loads(self.request.get('items'))
        for item in items:
            if "modifiers" in item:
                for mod in item["modifiers"]:
                    if mod["amount"] == 0:
                        mod["amount"] = 1

        if venue_id == Venue.COFFEE_CITY:
            items = fix_syrop.set_syrop_items(items)
            items = fix_modifiers_by_own.set_modifier_by_own(venue_id, items)

        order.items = items
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

        self._do_promos(company_id, order)

        # pay after pre check
        order_id = None
        if payment_type == '2':
            tie_result = tie_card(company, int(float(order_sum) * 100), int(time.time()), 'returnUrl', alpha_client_id,
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
        order.created_in_iiko = iiko_api.parse_iiko_time(result['createdTime'], venue)

        order.put()

        if venue_id == Venue.ORANGE_EXPRESS:
            send_express_email(order, customer, venue)

        resp = {
            'customer_id': customer.customer_id,
            'order': {
                'order_id': order.order_id,
                'status': order.status,
                'items': order.items,
                'sum': order.sum,
                # 'discount_sum': order.discount_sum,  # TODO
                'number': order.number,
                'venue_id': order.venue_id,
                'address': order.address,
                'date': int(self.request.get('date')),
                },
            'error_code': 0,
            # 'promos': promos  # TODO
        }

        self.render_json(resp)


class OrderInfoRequestHandler(base.BaseHandler):
    """ /api/order/%s """
    def get(self, order_id):
        order = iiko.Order.order_by_id(order_id)
        order.reload()

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

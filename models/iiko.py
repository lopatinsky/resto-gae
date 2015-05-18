# coding=utf-8
import logging
from google.appengine.ext import ndb
from google.appengine.api import memcache
import time
from methods import maps
from methods.maps import get_address_coordinates
from methods.parse_com import send_push, IOS_DEVICE, ANDROID_DEVICE, make_order_push_data


class PaymentType(ndb.Model):
    # payment types id
    CASH = '1'
    CARD = '2'

    name = ndb.StringProperty()
    type_id = ndb.IntegerProperty()
    iiko_uuid = ndb.StringProperty()
    available = ndb.BooleanProperty()

    def to_dict(self):
        return {
            'type_id': self.type_id,
            'name': self.name,
            'iiko_uuid': self.iiko_uuid,
            'available': self.available
        }


class DeliveryType(ndb.Model):
    delivery_id = ndb.IntegerProperty()
    name = ndb.StringProperty()
    available = ndb.BooleanProperty()

    def to_dict(self):
        return {
            'type_id': self.delivery_id,
            'name': self.name,
            'available': self.available
        }


class AvailableConfirmation(ndb.Model):
    requested_phone = ndb.StringProperty(required=True)
    code = ndb.IntegerProperty(required=True)


class Customer(ndb.Model):
    phone = ndb.StringProperty()
    name = ndb.StringProperty(indexed=False)
    user_agent = ndb.StringProperty()
    customer_id = ndb.StringProperty()
    custom_data = ndb.JsonProperty()

    confirmations = ndb.StructuredProperty(AvailableConfirmation, repeated=True)
    confirmed_phones = ndb.StringProperty(repeated=True)

    @classmethod
    def customer_by_phone(cls, phone):
        return cls.query(cls.phone == phone).get()

    @classmethod
    def customer_by_customer_id(cls, customer_id):
        return cls.query(cls.customer_id == customer_id).get()

    def get_device(self):
        if not self.user_agent:
            return
        if 'Android' in self.user_agent:
            return ANDROID_DEVICE
        elif 'iOS' in self.user_agent:
            return IOS_DEVICE


class Order(ndb.Model):
    # statuses
    UNKNOWN = -1
    NOT_APPROVED = 1
    APPROVED = 2
    CLOSED = 3
    CANCELED = 4

    # payment types
    CASH = '1'
    CARD = '2'

    STATUS_MAPPING = {
        NOT_APPROVED: [
            u'не подтверждена',
            'waiting for confirmation',
            'not confirmed',
        ],
        APPROVED: [
            u'новая',
            'new',
            u'ждет отправки',
            u'в пути',
            'on the way',
            u'готовится',
            'in progress',
            u'готово',
            'ready',
        ],
        CLOSED: [
            u'закрыта',
            'closed',
            u'доставлена',
            'delivered',
        ],
        CANCELED: [
            u'отменена',
            'cancelled',
        ]
    }

    PUSH_STATUSES = {
        UNKNOWN: u"Неизвестно",
        NOT_APPROVED: u"Ожидает подтверждения",
        APPROVED: u"Подтвержден",
        CANCELED: u"Отменен",
        CLOSED: u"Выполнен"
    }

    date = ndb.DateTimeProperty()
    sum = ndb.FloatProperty(indexed=False)
    discount_sum = ndb.FloatProperty(default=0)
    bonus_sum = ndb.FloatProperty(default=0)
    items = ndb.JsonProperty()
    is_delivery = ndb.BooleanProperty(default=False)
    address = ndb.JsonProperty()
    venue_id = ndb.StringProperty()  # actually iiko organization id
    delivery_terminal_id = ndb.StringProperty()
    customer = ndb.KeyProperty()
    order_id = ndb.StringProperty()
    number = ndb.StringProperty()
    status = ndb.IntegerProperty()
    comment = ndb.StringProperty(indexed=False)
    payment_type = ndb.StringProperty(indexed=False)
    alfa_order_id = ndb.StringProperty(indexed=False)
    source = ndb.StringProperty(choices=('app', 'iiko'), default='app')
    created_in_iiko = ndb.DateTimeProperty()
    updated = ndb.DateTimeProperty(auto_now=True)
    cancel_requested = ndb.BooleanProperty(default=False, indexed=False)

    # TODO Need to check english statuses(may be incorrect)
    @classmethod
    def parse_status(cls, status):
        status = status.lower()

        for status_value, strings in cls.STATUS_MAPPING.items():
            for string in strings:
                if string in status:
                    return status_value

        logging.warning("Unknown status: %s", status)
        return cls.UNKNOWN

    def set_status(self, status):
        self.status = self.parse_status(status)

    @classmethod
    def order_by_id(cls, order_id):
        return cls.query(cls.order_id == order_id).get()

    def to_dict(self):
        serialized = {
            'orderId': self.order_id,
            'number': self.number,
            'status': self.status,
            'sum': self.sum,
            'items': self.items,
            'venueId': self.venue_id,
            'address': self.address
        }

        return serialized

    def admin_dict(self, images_map):
        customer = self.customer.get()
        for item in self.items:
            item['images'] = images_map.get(item['id'], [])
        return {
            'order_id': self.order_id,
            'number': self.number,
            'address': self.address,
            'createdDate': int(time.mktime(self.created_in_iiko.timetuple())),
            'deliveryDate': int(time.mktime(self.date.timetuple())),
            'client_id': customer.customer_id,
            'phone': customer.phone,
            'client_name': customer.name,
            'client_custom_data': customer.custom_data,
            'comment': self.comment,
            'sum': self.sum,
            'items': self.items,
            'venue_id': self.delivery_terminal_id,
            'status': self.status,
            'cancel_requested': self.cancel_requested,
        }

    def _handle_changes(self, changes):
        from methods.alfa_bank import pay_by_card, get_back_blocked_sum
        from models.specials import SharedBonus
        if self.source != 'app':
            return

        if 'status' in changes:
            if self.payment_type == '2':
                logging.info("order paid by card")

                company = CompanyNew.get_by_iiko_id(self.venue_id)

                if self.status == Order.CLOSED:
                    pay_result = pay_by_card(company, self.alfa_order_id, 0)
                    logging.info("pay")
                    logging.info(str(pay_result))
                    if 'errorCode' not in pay_result.keys() or str(pay_result['errorCode']) == '0':
                        bonus = SharedBonus.query(SharedBonus.recipient == self.customer,
                                                  SharedBonus.status == SharedBonus.READY).get()
                        if bonus:
                            company = CompanyNew.get_by_iiko_id(self.venue_id)
                            bonus.deactivate(company)
                        logging.info("pay succeeded")
                    else:
                        logging.warning("pay failed")

                elif self.status == Order.CANCELED:
                    cancel_result = get_back_blocked_sum(company, self.alfa_order_id)
                    logging.info("cancel")
                    logging.info(str(cancel_result))
                    if 'errorCode' not in cancel_result or str(cancel_result['errorCode']) == '0':
                        logging.info("cancel succeeded")
                    else:
                        logging.warning("cancel failed")

            customer = self.customer.get()
            device = customer.get_device()
            data = make_order_push_data(self.order_id, self.number, self.status, self.PUSH_STATUSES[self.status], device)
            send_push(channels=["order_%s" % self.order_id], data=data, device_type=device)

    @classmethod
    def _do_load_from_object(cls, order, order_id, org_id, iiko_order):
        company = CompanyNew.get_by_iiko_id(org_id)
        changes = {}

        def _attr(name, new_value=None):
            old_value = getattr(order, name)
            if not new_value:
                new_value = iiko_order[name]
            if old_value != new_value:
                changes[name] = old_value
                setattr(order, name, new_value)

        if not order:
            changes['order'] = None
            order = Order(order_id=order_id, venue_id=org_id, source='iiko')
            order.is_delivery = iiko_order['orderType']['orderServiceType'] == 'DELIVERY_BY_COURIER'
            customer = Customer.customer_by_customer_id(iiko_order['customerId'])
            order.customer = customer.key if customer else None  # TODO create customer

        _attr('sum')
        _attr('items')
        _attr('address')
        _attr('number')

        date = iiko_api.parse_iiko_time(iiko_order['deliveryDate'], company)
        _attr('date', date)

        created_time = iiko_api.parse_iiko_time(iiko_order['createdTime'], company)
        _attr('created_in_iiko', created_time)

        _attr('status', Order.parse_status(iiko_order['status']))

        logging.debug("changes in %s: %s", order_id, changes.keys())
        if changes:
            order._handle_changes(changes)
            if order.source == 'app':
                order.put()
        return order

    @classmethod
    def load_from_object(cls, iiko_order):
        order_id = iiko_order['orderId']
        org_id = iiko_order['organization']
        order = cls.order_by_id(order_id)
        return cls._do_load_from_object(order, order_id, org_id, iiko_order)

    @classmethod
    def _do_load(cls, order, order_id, org_id):
        iiko_order = iiko_api.order_info1(order_id, org_id)
        return cls._do_load_from_object(order, order_id, org_id, iiko_order)

    @classmethod
    def load(cls, order_id, org_id):
        order = cls.order_by_id(order_id)
        return cls._do_load(order, order_id, org_id)

    def reload(self):
        self._do_load(self, self.order_id, self.venue_id)


class DeliveryTerminal(ndb.Model):
    company_id = ndb.IntegerProperty()
    iiko_organization_id = ndb.StringProperty()
    active = ndb.BooleanProperty(default=False)
    name = ndb.StringProperty(indexed=False)
    phone = ndb.StringProperty(indexed=False)
    address = ndb.StringProperty(indexed=False)
    location = ndb.GeoPtProperty(indexed=False)

    item_stop_list = ndb.StringProperty(repeated=True)

    def dynamic_dict(self):
        return {
            'stop_list': {
                'items': self.item_stop_list
            }
        }

    def to_dict(self):
        company = CompanyNew.get_by_id(self.company_id)
        return {
            'venueId': self.key.id(),
            'name': self.name,
            'address': self.address,
            'latitude': self.location.lat,
            'longitude': self.location.lon,
            'logoUrl': '',
            'phone': self.phone,
            'payment_types': [x.to_dict() for x in ndb.get_multi(company.payment_types)]
        }

    @classmethod
    def get_any(cls, iiko_org_id):
        return cls.query(cls.iiko_organization_id == iiko_org_id, cls.active == True).get()


class IikoApiLogin(ndb.Model):
    @property
    def login(self):
        return self.key.id()

    password = ndb.StringProperty(indexed=False)


class CompanyNew(ndb.Model):
    COFFEE_CITY = "02b1b1f7-4ec8-11e4-80cc-0025907e32e9"
    EMPATIKA = "95e4a970-b4ea-11e3-8bac-50465d4d1d14"
    MIVAKO = "6a05d004-e03d-11e3-bae4-001b21b8a590"
    ORANGE_EXPRESS = "768c213e-5bc1-4135-baa3-45f719dbad7e"
    SUSHILAR = "a9d16dff-7680-43f1-b1a1-74784bc75f60"
    VENEZIA = "b4c224da-b1d2-11e4-80d8-002590dc3769"
    DIMASH = "d3b9ba12-ee62-11e4-80cf-d8d38565926f"

    iiko_login = ndb.StringProperty()
    iiko_org_id = ndb.StringProperty()

    address = ndb.StringProperty(indexed=False)
    latitude = ndb.FloatProperty(indexed=False)
    longitude = ndb.FloatProperty(indexed=False)

    delivery_types = ndb.KeyProperty(kind=DeliveryType, repeated=True)
    payment_types = ndb.KeyProperty(kind=PaymentType, repeated=True)
    menu = ndb.JsonProperty()

    app_name = ndb.StringProperty(repeated=True)  # TODO REMOVE: part of user-agent to identify app in alfa handler
    app_title = ndb.StringProperty()
    alpha_login = ndb.StringProperty(indexed=False)
    alpha_pass = ndb.StringProperty(indexed=False)
    card_button_text = ndb.StringProperty()
    card_button_subtext = ndb.StringProperty()

    is_iiko_system = ndb.BooleanProperty(default=False)
    new_endpoints = ndb.BooleanProperty(default=False)

    description = ndb.StringProperty()
    min_order_sum = ndb.IntegerProperty()
    email = ndb.StringProperty()
    support_emails = ndb.StringProperty(repeated=True)
    site = ndb.StringProperty()
    cities = ndb.StringProperty(repeated=True)
    phone = ndb.StringProperty()
    schedule = ndb.JsonProperty()
    icon1 = ndb.BlobProperty()
    icon2 = ndb.BlobProperty()
    icon3 = ndb.BlobProperty()
    icon4 = ndb.BlobProperty()
    company_icon = ndb.BlobProperty()
    color = ndb.StringProperty()
    analytics_key = ndb.StringProperty()

    ios_push_channel = ndb.StringProperty()
    android_push_channel = ndb.StringProperty()

    @classmethod
    def get_payment_types(cls, venue_id):
        venue = cls.get_by_iiko_id(venue_id)
        output = []
        for item in ndb.get_multi(venue.payment_types):
            output.append(item.to_dict())
        return output

    def get_payment_type(self, type_id):
        for item in ndb.get_multi(self.payment_types):
            if item.type_id == int(type_id):
                return item
        return None

    @classmethod
    def get_delivery_types(cls, org_id):
        org = cls.get_by_id(int(org_id))
        output = []
        for item in ndb.get_multi(org.delivery_types):
            output.append(item.to_dict())
        return output

    def get_news(self):
        return News.query(News.company_id == self.key.id(), News.active == True).get()

    @classmethod
    def get_by_iiko_id(cls, iiko_org_id):
        return cls.query(cls.iiko_org_id == iiko_org_id).get()

    def get_timezone_offset(self):
        result = memcache.get('venue_%s_timezone' % self.iiko_org_id)
        if not result:
            result = maps.get_timezone_by_coords(self.latitude, self.longitude)
            memcache.set('venue_%s_timezone' % self.iiko_org_id, result, time=24*3600)
        return result

    @classmethod
    def create(cls, login, password, company_id=None, org_id=None):
        from config import config

        IikoApiLogin.get_or_insert(login, password=password)

        c = cls(id=company_id)
        c.iiko_login = login

        if org_id:
            org = iiko_api.get_org(login, org_id)
            c.iiko_org_id = org_id
        else:
            org = iiko_api.get_orgs(login)[0]
            c.iiko_org_id = org['id']
        c.app_title = org['name']
        c.address = org['address'] or org['contact']['location']
        c.latitude, c.longitude = get_address_coordinates(c.address)

        delivery_types = [
            DeliveryType(available=True, delivery_id=1, name="delivery"),
            DeliveryType(available=False, delivery_id=2, name="self"),
        ]
        c.delivery_types = ndb.put_multi(delivery_types)

        payment_types = [
            PaymentType(available=True, type_id=1, name="cash", iiko_uuid="CASH"),
            PaymentType(available=config.DEBUG, type_id=2, name="card", iiko_uuid="ECARD")
        ]
        c.payment_types = ndb.put_multi(payment_types)

        if config.DEBUG:
            c.alpha_login = "empatika_autopay-api"
            c.alpha_pass = "empatika-autopay"
        c.put()

        return c


class ImageCache(ndb.Model):
    # key name is urlsafe_b64encoded image URL
    updated = ndb.DateTimeProperty(auto_now=True)
    last_modified = ndb.StringProperty(indexed=False)
    serving_url = ndb.StringProperty(indexed=False)


class News(ndb.Model):
    company_id = ndb.IntegerProperty(required=True)
    text = ndb.StringProperty(required=True, indexed=False)
    active = ndb.BooleanProperty(required=True, default=True)
    created_at = ndb.DateTimeProperty(auto_now_add=True, indexed=False)

    def dict(self):
        return {
            "id": self.key.id(),
            "text": self.text,
            "created_at": int(time.mktime(self.created_at.timetuple()))
        }


class ClientInfo(ndb.Model):
    company_id = ndb.IntegerProperty(required=True)
    phone = ndb.StringProperty()
    email = ndb.StringProperty()
    created_at = ndb.DateTimeProperty(auto_now_add=True)
    user_agent = ndb.StringProperty()
    customer = ndb.KeyProperty(Customer)

    def get_device(self):
        if not self.user_agent:
            return
        if 'Android' in self.user_agent:
            return ANDROID_DEVICE
        elif 'iOS' in self.user_agent:
            return IOS_DEVICE


from methods import iiko_api  # needed in some functions

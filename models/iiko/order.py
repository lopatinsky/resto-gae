# coding=utf-8
from datetime import time
import logging
from google.appengine.ext import ndb
from models.iiko.customer import Customer
from models.iiko.organization import CompanyNew

__author__ = 'dvpermyakov'


class OrderChangeLogEntry(ndb.Model):
    what = ndb.StringProperty(indexed=False)
    old = ndb.PickleProperty()
    new = ndb.PickleProperty()


class OrderChangeLog(ndb.Model):
    order_id = ndb.StringProperty()
    created = ndb.DateTimeProperty(auto_now_add=True)
    changes = ndb.StructuredProperty(OrderChangeLogEntry, repeated=True, indexed=False)


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
    COURIER_CARD = '3'

    PAYMENT_MAP = {
        CASH: u'Наличные',
        CARD: u'Карта',
        COURIER_CARD: u'Карта курьеру'
    }

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

    def _create_change_log(self, changes):
        if not changes:
            return None
        log = OrderChangeLog(order_id=self.order_id)
        log.changes = [OrderChangeLogEntry(what=name, old=old, new=getattr(self, name))
                       for name, old in changes.items()]
        log.put()
        return log

    def get_change_logs(self):
        return OrderChangeLog.query(OrderChangeLog.order_id == self.order_id) \
                             .order(-OrderChangeLog.created).fetch()

    def _handle_changes(self, changes):
        from methods.parse_com import make_order_push_data, send_push
        from methods.alfa_bank import pay_by_card, get_back_blocked_sum
        from models.specials import SharedBonus
        if self.source != 'app':
            return

        self._create_change_log(changes)

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
            send_push(channels=["order_%s" % self.order_id], data=data, device_type=device, order=self)

    @classmethod
    def _do_load_from_object(cls, order, order_id, org_id, iiko_order):
        from methods.rendering import parse_iiko_time
        company = CompanyNew.get_by_iiko_id(org_id)
        changes = {}

        no_new_value = object()

        def _attr(name, new_value=no_new_value):
            old_value = getattr(order, name)
            if new_value is no_new_value:
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

        new_sum = iiko_order['sum']
        for payment in iiko_order['payments']:
            if 'INET' in payment['paymentType']['code']:
                new_sum -= payment['sum']
        _attr('sum', new_sum)

        _attr('items')
        _attr('address')
        _attr('number')

        delivery_terminal_id = None
        if iiko_order['deliveryTerminal']:
            delivery_terminal_id = iiko_order['deliveryTerminal']['deliveryTerminalId']
        _attr('delivery_terminal_id', delivery_terminal_id)

        date = parse_iiko_time(iiko_order['deliveryDate'], company)
        _attr('date', date)

        created_time = parse_iiko_time(iiko_order['createdTime'], company)
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
        from methods.iiko.order import order_info1
        iiko_order = order_info1(order_id, org_id)
        return cls._do_load_from_object(order, order_id, org_id, iiko_order)

    @classmethod
    def load(cls, order_id, org_id):
        order = cls.order_by_id(order_id)
        return cls._do_load(order, order_id, org_id)

    def reload(self):
        self._do_load(self, self.order_id, self.venue_id)

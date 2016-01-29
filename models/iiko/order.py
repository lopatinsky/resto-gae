# coding=utf-8
from datetime import time
import logging
from google.appengine.ext import ndb

__author__ = 'dvpermyakov'


APP_SOURCE = 'app'
AUTO_APP_SOURCE = 'auto_app'
IIKO_SOURCE = 'iiko'
SOURCE_CHOICES = (APP_SOURCE, AUTO_APP_SOURCE, IIKO_SOURCE)


class OrderRate(ndb.Model):
    meal_rate = ndb.FloatProperty(required=True)
    service_rate = ndb.FloatProperty(required=True)
    comment = ndb.StringProperty()


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
    CREATING = -2
    UNKNOWN = -1
    NOT_APPROVED = 1
    APPROVED = 2
    CLOSED = 3
    CANCELED = 4

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
        ],
        CREATING: [
            u'создается'
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
    initial_sum = ndb.FloatProperty(indexed=False)
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
    status = ndb.IntegerProperty(default=CREATING)
    comment = ndb.StringProperty(indexed=False)
    payment_type = ndb.StringProperty(indexed=False)
    alfa_order_id = ndb.StringProperty(indexed=False)
    source = ndb.StringProperty(choices=SOURCE_CHOICES, default=APP_SOURCE)
    created_in_iiko = ndb.DateTimeProperty()
    created = ndb.DateTimeProperty(auto_now_add=True)
    updated = ndb.DateTimeProperty(auto_now=True)
    cancel_requested = ndb.BooleanProperty(default=False, indexed=False)
    rate = ndb.LocalStructuredProperty(OrderRate)

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

    def get_change_logs(self):
        return OrderChangeLog.query(OrderChangeLog.order_id == self.order_id).order(-OrderChangeLog.created).fetch()

    @classmethod
    def load_from_object(cls, iiko_order):
        from methods.orders.change import do_load
        order_id = iiko_order['orderId']
        org_id = iiko_order['organization']
        order = cls.order_by_id(order_id)
        return do_load(order, order_id, org_id, iiko_order)

    @classmethod
    def load(cls, order_id, org_id):
        from methods.orders.change import do_load
        order = cls.order_by_id(order_id)
        return do_load(order, order_id, org_id)

    def reload(self):
        from methods.orders.change import do_load
        return do_load(self, self.order_id, self.venue_id)

# coding=utf-8
from datetime import timedelta

from methods import working_hours
from models.iiko.company import CompanyNew

_TEN_PERCENT_ALWAYS_CATEGORIES = [
    u"Кофе на вынос",
]
_TEN_PERCENT_EXCLUDED_VENUES = {
    "f1516ef4-6224-a808-0153-3e5b7ba2af5b",
    "19776457-cf5e-73b9-0154-2b93e702d5c0",     # Moscow City
    "f1516ef4-6224-a808-0153-3e5b7ba2af5b",     # Park
}

_EVENING_CATEGORIES = [
    u"Хлеб",
    u"Граб-н-Гоу",
    u"Выпечка",
    u"Десерты (24 часа)",
    u"Сэндвичи",
    u"Кулинария",
    u"Пицца, тако, буррито",
    u"Пирожки",
]
_EVENING_SCHEDULE = {
    "dc12db4e-f192-c4d2-0152-d2c383885e4f": {  # Lesnaya 5
        "days": [1, 2, 3, 4, 5, 6, 7],
        "hours": "21-23"
    },
    "dc12db4e-f192-c4d2-0152-d2c383885f6f": {  # Novinskiy 7
        "days": [1, 2, 3, 4, 5, 6, 7],
        "hours": "21-23"
    },
    "ce1b7218-7925-b427-0152-e0cb68223988": {  # Kuznetsky most
        "days": [1, 2, 3, 4, 5, 6, 7],
        "hours": "21-23"
    },
    "1bd13391-4c56-29b6-0152-ffeb8a0a30a2": {  # Paveletskaya
        "days": [1, 2, 3, 4, 5, 6, 7],
        "hours": "21-23"
    },
    "f1516ef4-6224-a808-0153-3e5b7ba2af5b": {  # Park
        "days": [1, 2, 3, 4, 5, 6, 7],
        "hours": "21-23"
    },
    "f1516ef4-6224-a808-0153-3e5b7ba2ab0e": {  # Michurinskiy
        "days": [1, 2, 3, 4, 5, 6, 7],
        "hours": "19-24"
    },
}


def _add_discount(order, item, discount_fraction):
    discount = discount_fraction * item['baseSum']
    item['discount_sum'] = discount
    item['sum'] -= discount
    order.discount_sum += discount


def apply_lpq_discounts(order):
    company = CompanyNew.get_by_iiko_id(order.venue_id)
    for item in order.items:
        if item['category'] in _TEN_PERCENT_ALWAYS_CATEGORIES \
                and order.delivery_terminal_id not in _TEN_PERCENT_EXCLUDED_VENUES:
            _add_discount(order, item, 0.1)
        elif item['category'] in _EVENING_CATEGORIES:
            if order.delivery_terminal_id in _EVENING_SCHEDULE:
                schedule = [_EVENING_SCHEDULE[order.delivery_terminal_id]]
                local_date = order.date + timedelta(seconds=company.get_timezone_offset())
                if working_hours.is_datetime_valid(schedule, local_date, order.is_delivery):
                    _add_discount(order, item, 0.3)

# coding=utf-8
from datetime import timedelta

from methods import working_hours
from models.iiko.company import CompanyNew

_TEN_PERCENT_ALWAYS_CATEGORIES = [
    "b934ff20-8f86-46d2-b438-090b8fc3c0cf",
    "2b29605c-f184-4409-a56b-c444db587a38",
]

_EVENING_CATEGORIES = [
    "9d1a068a-fdd5-46e8-bfbf-17f7512fc648",
    "a7b9dcc0-9650-42dc-bdd1-4cdcd650b879",
    "6a8d7a61-88f6-42eb-9d95-99cf71060d38",
]
_EVENING_PRODUCT_CODES = ["501188", "501187", "103085"]
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
    }
}


def _add_discount(order, item, discount_fraction):
    discount = discount_fraction * item['sum']
    item['discount_sum'] = discount
    item['sum'] -= discount
    order.discount_sum += discount


def apply_lpq_discounts(order):
    company = CompanyNew.get_by_iiko_id(order.venue_id)
    for item in order.items:
        if item['ext_category_id'] in _TEN_PERCENT_ALWAYS_CATEGORIES:
            _add_discount(order, item, 0.1)
        elif item['ext_category_id'] in _EVENING_CATEGORIES or item['code'] in _EVENING_PRODUCT_CODES:
            if order.delivery_terminal_id in _EVENING_SCHEDULE:
                schedule = [_EVENING_SCHEDULE[order.delivery_terminal_id]]
                local_date = order.date + timedelta(seconds=company.get_timezone_offset())
                if working_hours.is_datetime_valid(schedule, local_date, order.is_delivery):
                    _add_discount(order, item, 0.3)

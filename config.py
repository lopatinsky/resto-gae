# coding=utf-8

from google.appengine.api import app_identity
from methods import restrictions
from models.iiko import CompanyNew


class RestoConfig(object):
    pass


class ProductionConfig(RestoConfig):
    ALFA_BASE_URL = "https://engine.paymentgate.ru/payment"
    CHECK_SCHEDULE = False
    RESTRICTIONS = []
    BRANCH_IO_TAG = 'production'


class TestingConfig(RestoConfig):
    ALFA_BASE_URL = "https://test.paymentgate.ru/testpayment"
    CHECK_SCHEDULE = True
    RESTRICTIONS = [
        {
            'method': restrictions.restrict_product_by_time,
            'venues': {
                CompanyNew.EMPATIKA: [
                    {
                        'category_id': '2f38c84f-c70b-4d4d-8fc9-0d8ad087c056',
                        'schedule': [
                            {
                                'hours': '0-0',
                                'days': []
                            }
                        ]
                    }
                ]
            }
        }
    ]
    BRANCH_IO_TAG = 'test'
    GIFT_BRANCH_VENUES = [
        CompanyNew.EMPATIKA,
        CompanyNew.COFFEE_CITY
    ]
    INVITATION_BRANCH_VENUES = [
        CompanyNew.EMPATIKA,
        CompanyNew.COFFEE_CITY
    ]


if app_identity.get_application_id() == "empatika-resto":
    config = ProductionConfig()
else:
    config = TestingConfig()

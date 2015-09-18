# coding=utf-8

from google.appengine.api import app_identity


class RestoConfig(object):
    pass


class ProductionConfig(RestoConfig):
    ALFA_BASE_URL = "https://engine.paymentgate.ru/payment"
    CHECK_SCHEDULE = True
    DEBUG = False

    ERROR_EMAILS = {
        "server": "admins",
        "iiko": "admins",
        "address": "admins"
    }


class TestingConfig(RestoConfig):
    ALFA_BASE_URL = "https://test.paymentgate.ru/testpayment"
    CHECK_SCHEDULE = True
    DEBUG = True

    ERROR_EMAILS = {
        "address": "admins"
    }


if app_identity.get_application_id() == "empatika-resto":
    config = ProductionConfig()
else:
    config = TestingConfig()

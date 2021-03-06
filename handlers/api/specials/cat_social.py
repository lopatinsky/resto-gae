# coding=utf-8
import logging
from ..base import BaseHandler
from methods.iiko.customer import get_customer_by_phone, get_customer_by_id, create_or_update_customer
from methods.rendering import filter_phone
from models.iiko import CompanyNew, DeliveryTerminal
from models.specials import CATSocialId


class CATAddSocialHandler(BaseHandler):
    def render_error(self, message):
        logging.info(message)
        self.response.set_status(400)
        self.render_json({'description': message})

    def post(self):
        company_id = self.request.get_range('company_id')
        if not company_id:
            delivery_terminal_id = self.request.get('venue_id')
            company_id = DeliveryTerminal.get_by_id(delivery_terminal_id).company_id
        company = CompanyNew.get_by_id(company_id)
        if company.iiko_org_id not in (CompanyNew.COFFEE_CITY, CompanyNew.EMPATIKA):
            self.render_error("Unknown company")
            return

        customer_id = self.request.get('customer_id')
        phone = filter_phone(self.request.get('phone'))
        provider = self.request.get('provider')
        social_id = self.request.get('social_id')

        # 1: check if this social id was already used
        same_social_id = CATSocialId.query(CATSocialId.venue_id == company.iiko_org_id,
                                           CATSocialId.provider == provider,
                                           CATSocialId.social_id == social_id).get()
        if same_social_id:
            self.render_error(u"Данная учетная запись в социальной сети уже была привязана")
            return

        # 2: get customer info from iiko (this attempts to get customer_id if we only have phone)
        if not customer_id:
            iiko_customer = get_customer_by_phone(company, phone)
            if 'httpStatusCode' in iiko_customer:
                iiko_customer = {'phone': phone, 'balance': 0}
            customer_id = iiko_customer.get('id')
        else:
            iiko_customer = get_customer_by_id(company, customer_id)

        # 3: if we got customer_id, check if this customer already has an account of this provider
        if customer_id:
            same_customer_and_provider = CATSocialId.query(CATSocialId.venue_id == company.iiko_org_id,
                                                           CATSocialId.customer_id == customer_id,
                                                           CATSocialId.provider == provider).get()
            if same_customer_and_provider:
                self.render_error(u"Вы уже привязывали учетную запись в этой социальной сети")
                return

        # 4: add points
        iiko_customer['balance'] += 20
        customer_id = create_or_update_customer(company, iiko_customer)

        CATSocialId(venue_id=company.iiko_org_id, customer_id=customer_id, provider=provider, social_id=social_id).put()
        self.render_json({'customer_id': customer_id, 'balance': iiko_customer['balance']})


class CATFetchCoffeeShopsHandler(BaseHandler):
    def get(self):
        # Прости меня, Миша, но я хуй знает, как мы потом будем связывать эти места с чем-нибудь ещё в базе,
        # поэтому хардкожу всё это дело до лучших времён.
        self.render_json({
            'places': [
                {
                    'address': 'Ул. Мясницкая, 16',
                    'phone': '+00000000000',
                    'info': 'пн-пт 08:00-22:00 / сб-вс 10:00-22:00',
                    'name': 'Ул. Мясницкая, 16',
                    'coordinates': {
                        'lat': 55.760893,
                        'lng': 37.632404
                    }
                },
                {
                    'address': 'ул. Большая Новодмитровская, 36, стр. 1',
                    'phone': '+00000000000',
                    'info': 'пн-пт 10:00-21:00',
                    'name': 'Дизайн-завод Флакон',
                    'coordinates': {
                        'lat': 55.805120,
                        'lng': 37.587496
                    }
                },
                {
                    'address': 'ул. Тверская, 16, стр. 1',
                    'phone': '+00000000000',
                    'info': 'пн-пт 8:00-21:00 / сб-вс 11:00-21:00',
                    'name': 'ТДЦ Галерея Актёр',
                    'coordinates': {
                        'lat': 55.764635,
                        'lng': 37.606913
                    }
                }
            ]})


class CATGetCompanyIdHandler(BaseHandler):
    def get(self):
        self.render_json({
            "company_id": 0,
            "base_url": "http://example.com/"
        })


class CATGetCompanyIdHandler2(BaseHandler):
    def get(self):
        self.render_json({
            "company_id": 777,
            "base_url": "http://empatika-resto-test.appspot.com/api/"
        })

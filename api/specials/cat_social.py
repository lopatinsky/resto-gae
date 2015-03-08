# coding=utf-8
from ..base import BaseHandler
from methods import filter_phone, iiko_api
from models.iiko import Venue
from models.specials import CATSocialId


class CATAddSocialHandler(BaseHandler):
    def post(self):
        venue_id = self.request.get('venue_id')
        if venue_id not in (Venue.COFFEE_CITY, Venue.EMPATIKA):
            self.abort(400)
        company_id = Venue.venue_by_id(venue_id).company_id

        customer_id = self.request.get('customer_id')
        phone = filter_phone(self.request.get('phone'))
        provider = self.request.get('provider')
        social_id = self.request.get('social_id')

        # 1: check if this social id was already used
        same_social_id = CATSocialId.query(CATSocialId.venue_id == venue_id,
                                           CATSocialId.provider == provider,
                                           CATSocialId.social_id == social_id).get()
        if same_social_id:
            self.response.set_status(400)
            self.render_json({'description': u"Данная учетная запись в социальной сети уже была привязана"})
            return

        # 2: get customer info from iiko (this attempts to get customer_id if we only have phone)
        if not customer_id:
            iiko_customer = iiko_api.get_customer_by_phone(company_id, phone, venue_id)
            if 'httpStatusCode' in iiko_customer:
                iiko_customer = {'phone': phone, 'balance': 0}
            customer_id = iiko_customer.get('id')
        else:
            iiko_customer = iiko_api.get_customer_by_id(company_id, customer_id, venue_id)

        # 3: if we got customer_id, check if this customer already has an account of this provider
        if customer_id:
            same_customer_and_provider = CATSocialId.query(CATSocialId.venue_id == venue_id,
                                                           CATSocialId.customer_id == customer_id,
                                                           CATSocialId.provider == provider).get()
            if same_customer_and_provider:
                self.response.set_status(400)
                self.render_json({'description': u"Вы уже привязывали учетную запись в этой социальной сети"})
                return

        # 4: add points
        iiko_customer['balance'] += 20
        customer_id = iiko_api.create_or_update_customer(company_id, venue_id, iiko_customer)

        CATSocialId(venue_id=venue_id, customer_id=customer_id, provider=provider, social_id=social_id).put()
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
                    'address': 'Ул. Мясницкая, 16',
                    'phone': '+00000000000',
                    'info': 'пн-пт 08:00-22:00 / сб-вс 10:00-22:00',
                    'name': 'Ул. Мясницкая, 16',
                    'coordinates': {
                        'lat': 55.760893,
                        'lng': 37.632404
                    }
                }
            ]})
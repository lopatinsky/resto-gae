import logging
from google.appengine.api import memcache
from api.base import BaseHandler
from models.iiko import Venue, PaymentType

__author__ = 'mihailnikolaev'


class GetPaymentType(BaseHandler):

    """ /api/payment_type/<venue_id> """

    def get(self, venue_id):
        print venue_id
        return self.render_json({"types": Venue.get_payment_types(venue_id)})


class AddPaymentType(BaseHandler):

    """ /api/payment_type/add """

    def post(self):
        venue_id = self.request.get('venue_id')
        type_id = self.request.get('type_id')
        name = self.request.get('name')
        iiko_uuid = self.request.get('iiko_uuid')
        available = self.request.get('available')

        venue = Venue.venue_by_id(venue_id)
        pt = PaymentType.check_existence(type_id, iiko_uuid)

        if not pt:
            logging.info('No pt')
            pt = PaymentType()
            pt.name = name
            pt.type_id = int(type_id)
            pt.iiko_uuid = iiko_uuid
            pt.available = bool(available)
            pt.put()
        logging.info(pt)
        if not venue.check_ext(type_id):
            venue.payment_types.append(pt.key)
            venue.put()
            memcache.set('venue_%s' % venue.venue_id, venue, time=30*60)
            return self.render_json({
                'venue_id': venue.key.id(),
                'payment_type': type_id
            })
        else:
            return self.render_json({
                'error': 'payment type exist'
            })


class EditPaymentType(BaseHandler):

    """ /api/payment_type/edit """

    def post(self):
        type_id = self.request.get('type_id')
        name = self.request.get('name')
        available = self.request.get('available')
        iiko_uuid = self.request.get('iiko_uuid')

        pt = PaymentType.check_existence(type_id, iiko_uuid)

        if pt:
            if name:
                pt.name = name
            if available:
                pt.available = bool(available)
            if iiko_uuid:
                pt.iiko_uuid = iiko_uuid
            pt.put()
        else:
            return self.render_json({
                'error': 'invalid data',
                'code': 404
            })
        return self.render_json({
            'error': None,
            'code': 200
        })

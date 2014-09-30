from api import BaseHandler
from models.iiko import Company, DeliveryType

__author__ = 'mihailnikolaev'


class GetAvailableDeliveryTypesHandler(BaseHandler):

    """ /api/delivery_types """

    def get(self):
        org_id = self.request.get('organization_id')

        return self.render_json({"types": Company.get_delivery_types(org_id)})


class AddDeliveryType(BaseHandler):

    """ /api/delivery_type/add """

    def post(self):
        org_id = self.request.get('organization_id')
        delivery_id = self.request.get('type_id')
        available = self.request.get('available')
        name = self.request.get('name')

        company = Company.get_by_id(int(org_id))

        dt = DeliveryType.check_existence(int(delivery_id))

        if not dt:
            dt = DeliveryType()
            dt.delivery_id = int(delivery_id)
            dt.available = bool(available)
            dt.name = name
            dt.put()

        if not company.check_ext(delivery_id):
            company.delivery_types.append(dt.key)
            company.put()
            return self.render_json({
                'company': company.get_id(),
                'delivery_type': name
            })
        else:
            return self.render_json({
                'error': 'delivery type exists'
            })
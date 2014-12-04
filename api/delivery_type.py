# coding=utf-8

from .base import BaseHandler
from models.iiko import Company


class GetAvailableDeliveryTypesHandler(BaseHandler):

    """ /api/delivery_types """

    def get(self):
        org_id = self.request.get('organization_id')

        return self.render_json({"types": Company.get_delivery_types(org_id)})

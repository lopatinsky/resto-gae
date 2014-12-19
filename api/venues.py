# coding=utf-8

import json

import webapp2

from models.iiko import Company
from methods import iiko_api


class VenuesHandler(webapp2.RequestHandler):
    """ /api/venues/%s """

    def get(self, organization_id):
        company = Company.get_by_id(int(organization_id))

        if not company:
            return self.abort(403)

        venues = iiko_api.get_venues(company.get_id())
        self.response.headers['Content-Type'] = 'application/json'
        self.response.out.write(json.dumps({
            'venues': [venue.to_dict() for venue in venues]
        }))

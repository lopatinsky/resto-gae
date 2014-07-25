import json
import webapp2
import iiko
from iiko import Company, requests

__author__ = 'quiker'


class VenuesHandler(webapp2.RequestHandler):
    """ /api/venues/%s """

    def get(self, organization_id):
        company = Company.get_by_id(int(organization_id))

        if not company:
            return self.abort(403)

        requests.get_organization_token(company.get_id())
        venues = iiko.get_venues(company.get_id())
        self.response.headers['Content-Type'] = 'application/json'
        self.response.out.write(json.dumps({
            'venues': [venue.to_dict() for venue in venues]
        }))
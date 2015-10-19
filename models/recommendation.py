from google.appengine.ext import ndb
from models.iiko import CompanyNew

__author__ = 'dvpermyakov'


class Recommendation(ndb.Model):
    company = ndb.KeyProperty(kind=CompanyNew)
    item_id = ndb.StringProperty(required=True)
    recommendations = ndb.StringProperty(repeated=True, indexed=False)  # item_ids

    def dict(self):
        from methods.iiko.menu import get_product_from_menu
        org_id = self.company.get().iiko_org_id
        return {
            'items': [get_product_from_menu(org_id, product_id=recommendation)
                      for recommendation in self.recommendations]
        }

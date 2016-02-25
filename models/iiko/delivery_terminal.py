from google.appengine.ext import ndb
from models.iiko.company import CompanyNew

__author__ = 'dvpermyakov'


class DeliveryTerminal(ndb.Model):
    company_id = ndb.IntegerProperty()
    iiko_organization_id = ndb.StringProperty()
    active = ndb.BooleanProperty(default=False)
    name = ndb.StringProperty(indexed=False)
    phone = ndb.StringProperty(indexed=False)
    address = ndb.StringProperty(indexed=False)
    location = ndb.GeoPtProperty(indexed=False)
    schedule = ndb.JsonProperty()
    holiday_schedule = ndb.StringProperty(indexed=False, default='')

    item_stop_list = ndb.StringProperty(repeated=True)

    def dynamic_dict(self):
        return {
            'stop_list': {
                'items': self.item_stop_list
            }
        }

    def to_dict(self):
        company = CompanyNew.get_by_id(self.company_id)
        return {
            'active': self.active,
            'venueId': self.key.id(),
            'name': self.name,
            'address': self.address,
            'latitude': self.location.lat,
            'longitude': self.location.lon,
            'logoUrl': '',
            'phone': self.phone,
            'payment_types': [x.to_dict() for x in ndb.get_multi(company.payment_types)],
            'schedule': self.schedule or company.schedule,
        }

    @classmethod
    def get_any(cls, iiko_org_id):
        return cls.query(cls.iiko_organization_id == iiko_org_id, cls.active == True).get()
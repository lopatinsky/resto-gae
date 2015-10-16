from handlers.api.base import BaseHandler
from methods.iiko.menu import get_product_from_menu
from models.iiko import CompanyNew
from models.recommendation import Recommendation

__author__ = 'dvpermyakov'


class ItemRecommendationHandler(BaseHandler):
    def get(self):
        item_id = self.request.get('item_id')
        company_id = self.request.get_range('company_id')
        company = CompanyNew.get_by_id(company_id)
        if not company:
            self.abort(400)
        item = get_product_from_menu(company.iiko_org_id, product_id=item_id)
        if not item:
            self.abort(400)
        recommendation = Recommendation.query(Recommendation.item_id == item_id).get()
        self.render_json(recommendation.dict())
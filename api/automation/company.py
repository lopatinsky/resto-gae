__author__ = 'dvpermyakov'

import json
from ..base import BaseHandler
from models import iiko


class CreateCompanyHandler(BaseHandler):
    def post(self):
        company_info = json.loads(self.request.get('company_info'))

        company_params = {
            'app_name': company_info.get('app_title'),
            'description': company_info.get('about_text'),
            'min_order_sum': int(company_info.get('min_amount')),
            'cities': company_info.get('delivery_cities').split(','),
            'phone': company_info.get('phone'),
            'schedule': company_info.get('schedule'),
            'email': company_info.get('email'),
            'site': company_info.get('site'),
            'icons': company_info.get('icons'),
            'company_icon': company_info.get('icon_about'),
            'color': company_info.get('color'),
            'analytics_key': company_info.get('analytics_code')
        }

        company = iiko.Company(**company_params)
        company.put()

        id_json = {
            'id': company.key.id()
        }

        return self.render_json(id_json)


class GetCompanyHandler(BaseHandler):
    def get(self):
        company_id = self.request.get_range('company_id')
        company = iiko.Company.get_by_id(company_id)
        company_json = {
            'description': company.description,
            'min_order_sum': None,
            'contact': None,
            'cities': None,
        }
        return self.render_json(company_json)
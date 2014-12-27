__author__ = 'dvpermyakov'

import json
from ..base import BaseHandler
from models import iiko


class CreateOrUpdateCompanyHandler(BaseHandler):
    def post(self):
        company_info = json.loads(self.request.get('company_info'))
        company_id = self.request.get_range('company_id')

        company_params = {
            'app_name': company_info.get('app_title', None),
            'description': company_info.get('about_text', None),
            'min_order_sum': int(company_info['min_amount']) if company_info.get('min_amount') else None,
            'cities': company_info['delivery_cities'].split(',') if company_info.get('delivery_cities') else None,
            'phone': company_info.get('phone', None),
            'schedule': company_info.get('schedule', None),
            'email': company_info.get('email', None),
            'site': company_info.get('site', None),
            'icons': company_info.get('icons', None),
            'company_icon': company_info.get('icon_about', None),
            'color': company_info.get('color', None),
            'analytics_key': company_info.get('analytics_code', None)
        }

        if company_id:
            company = iiko.Company.get_by_id(company_id)
            if company_params['app_name']:
                company.app_name = company_params['app_name']
            if company_params['description']:
                company.description = company_params['description']
            if company_params['min_order_sum']:
                company.min_order_sum = company_params['min_order_sum']
            if company_params['cities']:
                company.cities = company_params['cities']
            if company_params['phone']:
                company.phone = company_params['phone']
            if company_params['schedule']:
                company.schedule = company_params['schedule']
            if company_params['email']:
                company.email = company_params['email']
            if company_params['site']:
                company.site = company_params['site']
            if company_params['icons']:
                company.icons = company_params['icons']
            if company_params['company_icon']:
                company.company_icon = company_params['company_icon']
            if company_params['color']:
                company.color = company_params['color']
            if company_params['analytics_key']:
                company.analytics_key = company_params['analytics_key']
        else:
            company = iiko.Company(**company_params)

        company.put()

        id_json = {
            'id': company.key.id()
        }

        return self.render_json(id_json)


class GetCompanyHandler(BaseHandler):
    def get(self):
        company_id = self.request.get_range('company_id')
        format = self.request.get('format', 'web')
        company = iiko.Company.get_by_id(company_id)
        company_json = {
            'company_id': company.key.id(),
            'description': company.description,
            'min_order_sum': company.min_order_sum,
            'cities': company.cities,
            'phone': company.phone,
            'schedule': company.schedule,
            'email': company.email,
            'site': company.site,
        }
        return self.render_json(company_json)
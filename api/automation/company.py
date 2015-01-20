# -*- coding: utf-8 -*-

__author__ = 'dvpermyakov'

import json
from ..base import BaseHandler
from models import iiko
import xml.etree.ElementTree as ET
from lxml import etree
import zipfile
from StringIO import StringIO
from google.appengine.ext import db
from methods import iiko_api


class GetCompaniesHandler(BaseHandler):
    def get(self):
        companies = iiko.Company.query().fetch()
        company_list = []
        for company in companies:
            company_json = {
                'login': company.name,
                'password': company.password,
                'app_name': company.app_name,
                'company_id': company.key.id(),
                'description': company.description,
                'min_order_sum': company.min_order_sum,
                'cities': company.cities,
                'phone': company.phone,
                'schedule': company.schedule,
                'email': company.email,
                'support_emails': company.support_emails,
                'site': company.site,
                'color': company.color,
                'analytics_key': company.analytics_key,
            }
            company_list.append(company_json)
        self.render_json(company_list)


class CreateOrUpdateCompanyHandler(BaseHandler):
    def post(self):
        company_info = json.loads(self.request.get('company_info'))
        company_id = self.request.get('company_id')

        is_delivery = company_info.get('is_delivery') == 'true'
        is_self = company_info.get('is_self_pickup') == 'true'
        company_params = {
            'app_name': company_info.get('app_title', None),
            'description': company_info.get('about_text', None),
            'min_order_sum': int(company_info['min_amount']) if company_info.get('min_amount') else None,
            'cities': company_info['delivery_cities'].split(',') if company_info.get('delivery_cities') else None,
            'phone': company_info.get('phone', None),
            'schedule': company_info.get('schedule', None),
            'email': company_info.get('email', None),
            'support_emails': company_info['support_emails'] if company_info.get('support_emails') else None,
            'site': company_info.get('site', None),
            'color': company_info.get('color', None),
            'analytics_key': company_info.get('analytics_code', None),
        }

        if company_id and company_id != '-1':
            company_id = int(company_id)
            company = iiko.Company.get_by_id(company_id)
            if not company:
                self.abort(404)
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
            if company_params['color']:
                company.color = company_params['color']
            if company_params['analytics_key']:
                company.analytics_key = company_params['analytics_key']
            if company_params['support_emails']:
                company.support_emails = company_params['support_emails']
            for delivery_type in company.delivery_types:
                delivery_type = delivery_type.get()
                name = delivery_type.name
                if name == 'self':
                    delivery_type.available = is_self
                elif name == 'delivery':
                    delivery_type.available = is_delivery
                delivery_type.put()

        else:
            delivery_self = iiko.DeliveryType(delivery_id=1, name='self', available=is_self)
            delivery_self.put()
            delivery_pickup = iiko.DeliveryType(delivery_id=0, name='delivery', available=is_delivery)
            delivery_pickup.put()
            company = iiko.Company(**company_params)
            company.delivery_types.append(delivery_self.key)
            company.delivery_types.append(delivery_pickup.key)

        company.put()

        for iiko_venue in iiko_api.get_venues(str(company.key.id())):
            iiko_api.get_menu(iiko_venue['id'], force_reload=True, filtered=False)
            venue = iiko.Venue.venue_by_id(iiko_venue['id'])
            venue.payment_types = []
            for iiko_payment in iiko_api.get_payment_types(venue.venue_id)['PaymentTypes']:
                payment = iiko.PaymentType()
                payment.name = iiko_payment['name']
                payment.iiko_uuid = iiko_payment['code']
                if payment.iiko_uuid == 'CASH':
                    payment.type_id = 1
                elif payment.iiko_uuid == 'ECARD':
                    payment.type_id = 2
                else:
                    payment.type_id = 3
                payment.put()
                venue.payment_types.append(payment.key)
            venue.put()


        id_json = {
            'id': company.key.id()
        }
        return self.render_json(id_json)


class UploadIconsHandler(BaseHandler):
    def post(self):
        company_id = self.request.get_range('company_id')
        company = None
        if company_id:
            company = iiko.Company.get_by_id(company_id)
        if company:
            company.icon1 = db.Blob(self.request.get('icon1', None))
            company.icon2 = db.Blob(self.request.get('icon2', None))
            company.icon3 = db.Blob(self.request.get('icon3', None))
            company.icon4 = db.Blob(self.request.get('icon4', None))
            company.company_icon = db.Blob(self.request.get('company_icon', None))
            company.put()
        else:
            self.error(404)
        return self.render_json({'id': company.key.id()})


class DownloadIconsHandler(BaseHandler):
    def get(self):
        company_id = self.request.get_range('company_id')
        icon_type = self.request.get('type')
        company = None
        if company_id:
            company = iiko.Company.get_by_id(company_id)
        if company:
            self.response.headers['Content-Type'] = 'image/png'
            if icon_type == 'company_icon':
                self.response.out.write(company.company_icon)
            elif icon_type == 'icon1':
                self.response.out.write(company.icon1)
            elif icon_type == 'icon2':
                self.response.out.write(company.icon2)
            elif icon_type == 'icon3':
                self.response.out.write(company.icon3)
            elif icon_type == 'icon4':
                self.response.out.write(company.icon4)
            else:
                self.error(404)
        else:
            self.error(404)


class GetCompanyHandler(BaseHandler):

    def get_zip_file(self, zip_arch, string, file_name):
        input_stream = StringIO(string)
        input_stream.seek(0)
        buf = input_stream.read()
        while(buf):
            zip_arch.writestr(file_name, buf)
            buf = input_stream.read()
        return zip_arch

    @staticmethod
    def create_xml_element(root, elem_type, name, obj_type, text):
        key = ET.SubElement(root, elem_type)
        key.text = name
        obj = ET.SubElement(root, obj_type)
        obj.text = text
        return key, obj

    @staticmethod
    def create_key_xml(root, elem_type, name, prop=None):
        key = ET.SubElement(root, elem_type)
        key.text = name
        if prop:
            for prop_key in prop.keys():
                key.set(prop_key, prop[prop_key])
        return key

    def output_stream(self, output_stream):
        buf = output_stream.read()
        while buf:
            self.response.out.write(buf)
            buf = output_stream.read()

    def get(self):
        company_id = self.request.get_range('company_id')
        device_format = self.request.get('platform')
        file_format = self.request.get('file_format', 'json')
        company = iiko.Company.get_by_id(company_id)

        if file_format == 'json':
            company_json = {
                'app_name': company.app_name,
                'company_id': company.key.id(),
                'description': company.description,
                'min_order_sum': company.min_order_sum,
                'cities': company.cities,
                'phone': company.phone,
                'schedule': company.schedule,
                'email': company.email,
                'support_emails': company.support_emails,
                'site': company.site,
                'color': company.color,
                'analytics_key': company.analytics_key,
                'delivery_types': iiko.Company.get_delivery_types(company_id)
            }
            self.render_json(company_json)
            return

        if device_format == 'ios':
            s = """<?xml version="1.0" encoding="UTF-8"?>
                   <plist version="1.0"/>"""
            tree = etree.fromstring(s)
            main_dict = etree.SubElement(tree, 'dict')

            self.create_key_xml(main_dict, 'key', 'OrganizationInfo')
            child_dict = ET.SubElement(main_dict, 'dict')
            self.create_xml_element(child_dict, 'key', 'OrganizationId', 'string', str(company_id))
            self.create_xml_element(child_dict, 'key', 'OrganizationColor', 'integer', company.color)
            self.create_xml_element(child_dict, 'key', 'OrganizationGAKey', 'string', company.analytics_key)

            self.create_xml_element(child_dict, 'key', 'AppIconUrl', 'integer', 'None')
            self.create_xml_element(main_dict, 'key', 'CFBundleDevelopmentRegion', 'string', 'ru')
            self.create_xml_element(main_dict, 'key', 'CFBundleDisplayName', 'string', '${EXECUTABLE_NAME}')
            self.create_xml_element(main_dict, 'key', 'CFBundleIdentifier', 'string', 'com.empatika.resto')
            self.create_xml_element(main_dict, 'key', 'CFBundleInfoDictionaryVersion', 'string', '6.0')
            self.create_xml_element(main_dict, 'key', 'CFBundleName', 'string', '${PRODUCT_NAME}')
            self.create_xml_element(main_dict, 'key', 'CFBundlePackageType', 'string', 'APPL')
            self.create_xml_element(main_dict, 'key', 'CFBundleShortVersionString', 'string', '1.0')
            self.create_xml_element(main_dict, 'key', 'CFBundleSignature', 'string', '????')
            self.create_xml_element(main_dict, 'key', 'CFBundleVersion', 'string', '1.0}')
            self.create_xml_element(main_dict, 'key', 'LSApplicationCategoryType', 'string', '')
            self.create_xml_element(main_dict, 'key', 'LSRequiresIPhoneOS', 'true', '')
            self.create_xml_element(main_dict, 'key', 'UIMainStoryboardFile', 'string', 'Main')

            self.create_key_xml(main_dict, 'key', 'UIRequiredDeviceCapabilities')
            array = self.create_key_xml(main_dict, 'array', '')
            self.create_key_xml(array, 'string', 'armv7')
            self.create_key_xml(main_dict, 'key', 'UISupportedInterfaceOrientations')
            array = self.create_key_xml(main_dict, 'array', '')
            self.create_key_xml(array, 'string', 'UIInterfaceOrientationPortrait')

            doc_type = '<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">'
            raw_string = etree.tostring(tree, encoding='utf8', xml_declaration=True, pretty_print=True,
                                        doctype=doc_type)

            if file_format == 'xml':
                self.response.headers['Content-Type'] = 'application/xml'
                self.response.out.write(raw_string)
            elif file_format == 'zip':
                output_stream = StringIO()
                zip_arch = self.get_zip_file(zipfile.ZipFile(output_stream, 'w'), raw_string, 'ios.xml')
                zip_arch.close()
                self.response.headers['Content-Type'] = 'application/zip'
                self.response.headers['Content-Disposition'] = 'attachment; filename="ios.zip"'
                output_stream.seek(0)
                self.output_stream(output_stream)
            else:
                self.abort(404)

        elif device_format == 'android':
            s = '''<?xml version="1.0" encoding="UTF-8"?>
                   <values/>'''
            tree = etree.fromstring(s)

            self.create_key_xml(tree, 'string', company.app_name, {'name': 'app_name'})
            self.create_key_xml(tree, 'string', company.name, {'name': 'about_name'})
            self.create_key_xml(tree, 'string', company.app_name, {'name': 'about_time'})
            self.create_key_xml(tree, 'string', company.phone, {'name': 'about_phone'})
            self.create_key_xml(tree, 'string', company.description, {'name': 'about_description"'})
            self.create_key_xml(tree, 'string', company.site, {'name': 'about_site'})
            self.create_key_xml(tree, 'string', company.email, {'name': 'feedback_email'})
            emails = self.create_key_xml(tree, 'string-array', '', {'name': 'feedback_cc_email'})
            self.create_key_xml(emails, 'item', '')
            self.create_key_xml(emails, 'item', '')
            self.create_key_xml(tree, 'string', str(company.min_order_sum), {'name': 'minimalOrderPrice'})
            self.create_key_xml(tree, 'string', '%s rubles', {'name': 'price'})
            self.create_key_xml(tree, 'string', company.cities[0], {'name': 'searchAddress'})
            cities = self.create_key_xml(tree, 'string-array', '', {'name': 'cities'})
            for city in company.cities:
                self.create_key_xml(cities, 'item', city)

            raw_string = etree.tostring(tree, encoding='utf8', xml_declaration=True, pretty_print=True)
            output_stream = StringIO()
            zip_arch = self.get_zip_file(zipfile.ZipFile(output_stream, 'w'), raw_string, 'string.xml')

            s = '''<?xml version="1.0" encoding="UTF-8"?>
                   <resources/>'''

            tree = etree.fromstring(s)
            self.create_key_xml(tree, 'string', company.analytics_key)
            self.create_key_xml(tree, 'bool', 'true', {'name': 'ga_autoActivityTracking'})
            self.create_key_xml(tree, 'integer', '300', {'name': 'ga_sessionTimeout'})

            raw_string = etree.tostring(tree, encoding='utf8', xml_declaration=True, pretty_print=True)

            if file_format == 'xml':
                self.response.headers['Content-Type'] = 'application/xml'
                self.response.out.write(raw_string)
            elif file_format == 'zip':
                zip_arch = self.get_zip_file(zip_arch, raw_string, 'global_tracker.xml')
                zip_arch.close()
                output_stream.seek(0)
                self.response.headers['Content-Type'] = 'application/zip'
                self.response.headers['Content-Disposition'] = 'attachment; filename="android.zip"'
                self.output_stream(output_stream)
            else:
                self.abort(404)
# coding=utf-8
from datetime import datetime, timedelta, date, time
from ..base import BaseHandler
from methods import excel


class BaseReportHandler(BaseHandler):
    def render_report(self, report_name, html_values):
        if self.request.get("button") == "xls":
            excel.send_excel_file(self, report_name, report_name + '.html', **html_values)
        else:
            self.render('/reports/%s.html' % report_name, **html_values)

    def get_date_range(self):
        try:
            start = datetime.strptime(self.request.get("start"), "%Y-%m-%d")
            end = datetime.strptime(self.request.get("end"), "%Y-%m-%d")
        except ValueError:
            start = end = datetime.combine(date.today(), time())
        end = end + timedelta(days=1) - timedelta(microseconds=1)
        return start, end

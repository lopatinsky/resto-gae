__author__ = 'dvpermyakov'

from ..base import BaseHandler
from venue import VenueReportHandler


class ReportHandler(BaseHandler):
    def get(self):
        self.render('report.html')
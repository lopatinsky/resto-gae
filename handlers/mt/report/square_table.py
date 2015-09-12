from datetime import datetime
from ..base import BaseHandler
from models.iiko import CompanyNew
from models.square_table import JsonStorage


class SquareTableHandler(BaseHandler):
    def get(self):
        square_list = JsonStorage.get("square_table")
        companies = CompanyNew.query().fetch()
        if square_list:
            for square in square_list.values():
                for row in square:
                    for cell in row:
                        cell["begin"] = datetime.fromtimestamp(cell["begin"])
                        cell["end"] = datetime.fromtimestamp(cell["end"])
            company_id = self.request.get_range('selected_company')
            if not company_id:
                company_id = CompanyNew.get_by_iiko_id(CompanyNew.ORANGE_EXPRESS).key.id()
            self.render('reports/square_table.html', square=square_list,
                        chosen_company=CompanyNew.get_by_id(company_id), companies=companies)
        else:
            self.response.write("Report not ready")

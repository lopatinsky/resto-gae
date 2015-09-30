from .base import GAEAuthBaseHandler
from models.iiko.company import CompanyNew


class ExportLegalsHandler(GAEAuthBaseHandler):
    ALLOWED_IDS = "rubeacon-legals",

    def get(self):
        result = []
        for c in CompanyNew.query().fetch():
            result.append({
                'id': c.iiko_org_id,
                'app_name': c.app_title,
                'name': c.app_title
            })
        self.render_json({"legals": result})

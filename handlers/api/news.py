# coding=utf-8
from handlers.api.base import BaseHandler
from models.iiko import CompanyNew
from models.specials import News

__author__ = 'dvpermyakov'


class NewsHandler(BaseHandler):
    def get(self, company_id):
        company = CompanyNew.get_by_id(int(company_id))
        news = News.get(company)
        self.render_json({
            "news": news.dict() if news else None,
            "card_button_text": company.card_button_text or u"Добавить карту",
            "card_button_subtext": company.card_button_subtext or "",
            'is_iiko': company.is_iiko_system or company.iiko_org_id == CompanyNew.TYKANO
        })

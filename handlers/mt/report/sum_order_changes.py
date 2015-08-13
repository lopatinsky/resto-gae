from datetime import datetime
from handlers.mt.base import BaseHandler
from handlers.mt.report.report_methods import suitable_date, PROJECT_STARTING_YEAR
from models.iiko import CompanyNew, Order, OrderChangeLog, PaymentType

__author__ = 'dvpermyakov'


class OrderSumChangesReport(BaseHandler):
    def get(self):
        org_id = self.request.get("selected_company")
        chosen_year = self.request.get_range("selected_year")
        chosen_month = self.request.get_range("selected_month")
        chosen_day = self.request.get_range("selected_day")
        if not chosen_year:
            chosen_month = 0
        if not chosen_month:
            chosen_day = 0
        if not org_id:
            chosen_year = datetime.now().year
            chosen_month = datetime.now().month
            chosen_day = 0
        start = suitable_date(chosen_day, chosen_month, chosen_year, True)
        end = suitable_date(chosen_day, chosen_month, chosen_year, False)
        change_dicts = []
        for company in (CompanyNew.query().fetch() if not org_id else [CompanyNew.query(CompanyNew.iiko_org_id == org_id).get()]):
            for order in Order.query(Order.venue_id == company.iiko_org_id,
                                     Order.date > start, Order.date < end).fetch():
                if order.status != Order.CLOSED:
                    continue
                for log in OrderChangeLog.query(OrderChangeLog.order_id == order.order_id).fetch():
                    for change in log.changes:
                        if change.what == 'sum':
                            change_dicts.append({
                                'company': company.app_title,
                                'day': order.date,
                                'number': order.number,
                                'status': Order.STATUS_MAPPING[order.status][0],
                                'type': PaymentType.PAYMENT_MAP[order.payment_type],
                                'old': change.old,
                                'new': change.new
                            })
        return self.render('/changelog/changes.html', **{
            'companies': CompanyNew.query().fetch(),
            'start_year': PROJECT_STARTING_YEAR,
            'end_year': datetime.now().year,
            'chosen_company': CompanyNew.get_by_iiko_id(org_id),
            'chosen_year': chosen_year,
            'chosen_month': chosen_month,
            'chosen_day': chosen_day,
            'changes': change_dicts
        })

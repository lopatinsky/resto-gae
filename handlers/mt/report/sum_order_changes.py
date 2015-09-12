from .base import BaseReportHandler
from models.iiko import CompanyNew, Order, OrderChangeLog, PaymentType

__author__ = 'dvpermyakov'


class OrderSumChangesReport(BaseReportHandler):
    def get(self):
        org_id = self.request.get("selected_company")
        if org_id == "0":
            org_id = None
        start, end = self.get_date_range()
        change_dicts = []
        for company in (CompanyNew.query().fetch() if not org_id else [CompanyNew.get_by_iiko_id(org_id)]):
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
        return self.render('reports/changes.html', **{
            'companies': CompanyNew.query().fetch(),
            'chosen_company': CompanyNew.get_by_iiko_id(org_id),
            'start': start,
            'end': end,
            'changes': change_dicts
        })

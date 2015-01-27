__author__ = 'dvpermyakov'

from ..base import BaseHandler
from datetime import datetime
from report_methods import suitable_date, PROJECT_STARTING_YEAR
from models import iiko
import calendar


class RepeatedOrdersReportHandler(BaseHandler):
    def get(self):
        venue_id = self.request.get("selected_venue")
        chosen_year = self.request.get_range("selected_year")
        chosen_month = self.request.get_range("selected_month")
        chosen_day = self.request.get_range("selected_day")
        if not chosen_year:
            chosen_month = 0
        if not chosen_month:
            chosen_day = 0
        if not venue_id:
            chosen_year = datetime.now().year
            chosen_month = datetime.now().month
            chosen_day = datetime.now().day
        if venue_id == '0':
            venue_id = None

        days = []
        total = {
            'new_number': 0,
            'old_number': 0,
            'new_sum': 0,
            'old_sum': 0
        }
        for day in range(1, calendar.monthrange(chosen_year, chosen_month)[1] + 1):
            new_number = 0
            old_number = 0
            new_sum = 0
            old_sum = 0
            start = suitable_date(day, chosen_month, chosen_year, True)
            end = suitable_date(day, chosen_month, chosen_year, False)
            query = iiko.Order.query(iiko.Order.date >= start, iiko.Order.date <= end,
                                     iiko.Order.status == iiko.Order.CLOSED)
            if venue_id:
                query.filter(iiko.Order.venue_id == venue_id)
            for order in query.fetch():
                customer_key = order.customer
                first_order = iiko.Order.query(iiko.Order.customer == customer_key,
                                               iiko.Order.status == iiko.Order.CLOSED)\
                    .order(iiko.Order.date).get()
                if first_order.key.id() == order.key.id():
                    new_number += 1
                    new_sum += order.sum
                else:
                    old_number += 1
                    old_sum += order.sum
            days.append({
                'day': day,
                'new_number': new_number,
                'old_number': old_number,
                'new_sum': new_sum,
                'old_sum': old_sum
            })
            total['new_number'] += new_number
            total['old_number'] += old_number
            total['new_sum'] += new_sum
            total['old_sum'] += old_sum

        values = {
            'venues': iiko.Venue.query().fetch(),
            'days': days,
            'total': total,
            'chosen_venue': iiko.Venue.venue_by_id(venue_id) if venue_id else None,
            'start_year': PROJECT_STARTING_YEAR,
            'end_year': datetime.now().year,
            'chosen_year': chosen_year,
            'chosen_month': chosen_month,
            'chosen_day': chosen_day
        }
        self.render('reported_repeated_orders.html', **values)
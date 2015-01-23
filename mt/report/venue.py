__author__ = 'dvpermyakov'

from ..base import BaseHandler
from models import iiko
from datetime import datetime
from report_methods import suitable_date, PROJECT_STARTING_YEAR


class VenueReportHandler(BaseHandler):
    def get(self):
        chosen_year = self.request.get("selected_year")
        chosen_month = self.request.get_range("selected_month")
        chosen_day = self.request.get_range("selected_day")

        if not chosen_year:
            chosen_year = datetime.now().year
            chosen_month = datetime.now().month
            chosen_day = datetime.now().day
        else:
            chosen_year = int(chosen_year)

        query = iiko.Order.query(iiko.Order.date >= suitable_date(chosen_day, chosen_month, chosen_year, True))
        query = query.filter(iiko.Order.date <= suitable_date(chosen_day, chosen_month, chosen_year, False))
        orders = query.fetch()

        venues = iiko.Venue.query().fetch()
        venue_ids = {}
        for venue in venues:
            venue.order_number = 0
            venue.closed_number = 0
            venue.closed_sum = 0
            venue.cancel_number = 0
            venue.cancel_sum = 0
            venue.delivery = 0
            venue.card = 0
            venue_ids[venue.venue_id] = venue
        for order in orders:
            venue = venue_ids[order.venue_id]
            venue.order_number += 1
            if order.status == iiko.Order.CLOSED:
                venue.closed_number += 1
                venue.closed_sum += order.sum
            elif order.status == iiko.Order.CANCELED:
                venue.cancel_number += 1
                venue.cancel_sum += order.sum
            if order.is_delivery:
                venue.delivery += 1
            if order.payment_type == 2:
                venue.card += 1

        values = {
            'venues': venue_ids.values(),
            'start_year': PROJECT_STARTING_YEAR,
            'end_year': datetime.now().year,
            'chosen_year': chosen_year,
            'chosen_month': chosen_month,
            'chosen_day': chosen_day
        }
        self.render('reported_venues.html', **values)

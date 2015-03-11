from datetime import datetime
from ..base import BaseHandler
from models.iiko import Venue
from models.square_table import JsonStorage


class SquareTableHandler(BaseHandler):
    def get(self):
        square_list = JsonStorage.get("square_table")
        venues = Venue.query().fetch()
        if square_list:
            for venue in venues:
                square = square_list.get(venue.venue_id)
                if not square:
                    continue
                for row in square:
                    for cell in row:
                        cell["begin"] = datetime.fromtimestamp(cell["begin"])
                        cell["end"] = datetime.fromtimestamp(cell["end"])
            venue_id = self.request.get_range('selected_venue')
            if not venue_id:
                venue_id = Venue.venue_by_id(Venue.ORANGE_EXPRESS).key.id()
            self.render('reported_square_table.html', square=square_list, chosen_venue=Venue.get_by_id(venue_id),
                        venues=venues)
        else:
            self.response.write("Report not ready")
# coding=utf-8
from collections import defaultdict, Counter
from datetime import date, timedelta, datetime
import logging
from google.appengine.ext import ndb
from webapp2 import RequestHandler
from methods.iiko.history import get_orders
from models.iiko.company import CompanyNew
from models.recommendation import Recommendation

DAYS_TO_FETCH = 3
RECOMMENDATION_COMPANIES = (CompanyNew.ORANGE_EXPRESS,)


class BuildRecommendationsHandler(RequestHandler):
    def get(self):
        today = date.today()
        start_date = today - timedelta(days=DAYS_TO_FETCH)
        for org_id in RECOMMENDATION_COMPANIES:
            company = CompanyNew.get_by_iiko_id(org_id)

            logging.debug("history fetch start")
            history = get_orders(company, start_date, today, 'CLOSED')['deliveryOrders']

            logging.debug("counting start")
            pair_order_count = defaultdict(Counter)  # item1_id -> (item2_id -> num of orders)
            for order in history:
                item_ids = set(item['id'] for item in order['items'])
                for item_id in item_ids:
                    for other_item_id in item_ids:
                        if other_item_id != item_id:
                            pair_order_count[item_id][other_item_id] += 1

            logging.debug("building objects")
            recs = []
            for item_id in pair_order_count:
                rec_ids = [rec_id for rec_id, count in pair_order_count[item_id].most_common(3)]
                recs.append(Recommendation(company=company.key, item_id=item_id,
                                           recommendations=rec_ids))

            logging.debug("fetching old rec keys")
            old_rec_keys = Recommendation.query(Recommendation.company == company.key).fetch(keys_only=True)

            logging.debug("removing old recs")
            ndb.delete_multi(old_rec_keys)

            logging.debug("putting new recs")
            ndb.put_multi(recs)
            logging.debug("finished")

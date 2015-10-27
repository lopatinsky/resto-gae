# coding=utf-8
from collections import defaultdict, Counter
from datetime import date, timedelta, datetime
import logging
from google.appengine.ext import ndb
from webapp2 import RequestHandler
from methods.iiko.history import get_orders
from methods.iiko.menu import list_menu
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

            logging.debug("building category dict")
            menu = list_menu(org_id)
            item_categories = {}
            for product in menu:
                item_categories[product['productId']] = product['categoryId']

            logging.debug("history fetch start")
            history = get_orders(company, start_date, today, 'CLOSED')['deliveryOrders']

            logging.debug("counting start")
            item_count_by_category = defaultdict(Counter)  # cat_id -> (item_id -> num of orders) for popular section
            pair_order_count = defaultdict(Counter)  # item1_id -> (item2_id -> num of orders)
            for order in history:
                item_ids = set(item['id'] for item in order['items'] if item['id'] in item_categories)
                for item_id in item_ids:
                    item_count_by_category[item_categories[item_id]][item_id] += 1
                    for other_item_id in item_ids:
                        if other_item_id != item_id:
                            k = 1
                            if item_categories[item_id] == item_categories[other_item_id]:
                                k = 0.2
                            pair_order_count[item_id][other_item_id] += k

            logging.debug("building global popular")
            popular_pairs = [c.most_common(1)[0] for c in item_count_by_category.values()]
            most_common = sorted(popular_pairs, key=lambda pair: pair[1], reverse=True)[:5]
            logging.info(most_common)

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

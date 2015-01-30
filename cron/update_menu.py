# coding=utf-8

import logging
from google.appengine.ext import deferred
from google.appengine.runtime import DeadlineExceededError
import webapp2
from models.iiko import Venue
from methods import iiko_api
from methods.image_cache import get_image


def _get_menu_images(menu):
    result = []

    def process_category(category):
        for image in category['image']:
            result.append(image['imageUrl'])
        for product in category['products']:
            result.extend(product['images'])
        for sub in category['children']:
            process_category(sub)

    for root_category in menu:
        process_category(root_category)

    result = [url.partition('/img/')[2]
              for url in result
              if '/static/' not in url]
    return filter(None, result)


def _defer_load_images(venue_id, image_number):
    logging.info("starting defer for %s", venue_id)
    images = _get_menu_images(Venue.venue_by_id(venue_id).menu)
    count = len(images)
    logging.info("progress: %s/%s", image_number, count)
    try:
        while image_number < count:
            image_url = str(images[image_number])
            get_image(image_url, force_fetch=True)
            image_number += 1
    except DeadlineExceededError:
        deferred.defer(_defer_load_images, venue_id, image_number)


class UpdateMenuHandler(webapp2.RequestHandler):
    def get(self):
        venues = Venue.query().fetch()
        for venue in venues:
            try:
                iiko_api.get_menu(venue.venue_id, force_reload=True)
                deferred.defer(_defer_load_images, venue.venue_id, 0)
            except Exception as e:
                logging.exception(e)

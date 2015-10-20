# coding=utf-8

import base64
import StringIO
import logging
from PIL import Image
from google.appengine.api import app_identity, blobstore, images, urlfetch
from lib import cloudstorage
from models.specials import ImageCache

MAX_SIZE = 750.
_BUCKET = app_identity.get_default_gcs_bucket_name()


def _fetch_image(url_base64, cache_info):
    url = base64.urlsafe_b64decode(url_base64)
    logging.info("image url: %s", url)
    headers = {}
    if cache_info:
        logging.info("image was cached")
        headers['If-Modified-Since'] = cache_info.last_modified

    response = urlfetch.fetch(url, headers=headers)
    logging.info("image fetched, status is %s", response.status_code)
    if response.status_code == 200:  # new or updated image
        logging.info("image is new or modified")
        image_data = response.content

        # resize
        image = Image.open(StringIO.StringIO(image_data))
        width, height = image.size
        logging.info("image size is %sx%s", width, height)
        if width > MAX_SIZE or height > MAX_SIZE:
            ratio = min(MAX_SIZE / width, MAX_SIZE / height)
            new_size = int(width * ratio), int(height * ratio)
            logging.info("resizing to %sx%s", *new_size)
            image = image.resize(new_size, Image.ANTIALIAS)

        # save to GCS
        filename = "/%s/%s" % (_BUCKET, url_base64)
        image_file = cloudstorage.open(filename, "w", "image/png")
        image.save(image_file, "PNG")
        image_file.close()

        # get serving url
        blob_key = blobstore.create_gs_key("/gs" + filename)
        serving_url = images.get_serving_url(blob_key, size=max(image.size), secure_url=False)

        # save cache info
        cache_info = ImageCache(
            id=url_base64,
            last_modified=response.headers["Last-Modified"],
            serving_url=serving_url
        )
        cache_info.put()
    elif response.status_code == 304:
        logging.info("image not modified")
        cache_info.put()  # refresh cache_info.updated
    else:
        return None
    return cache_info


def get_image(url_base64, force_fetch=False):
    cache_info = ImageCache.get_by_id(url_base64)
    if force_fetch or not cache_info:
        cache_info = _fetch_image(url_base64, cache_info)
    if not cache_info:  # error while loading
        return None
    return cache_info.serving_url


def convert_url(request, url):
    return request.host_url + "/img/" + base64.urlsafe_b64encode(url.replace('\\', ''))

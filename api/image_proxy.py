from .base import BaseHandler
from methods import image_cache


class ImageProxyHandler(BaseHandler):
    def get(self, url_base64):
        url = image_cache.get_image(url_base64)
        if not url:
            self.abort(500)
        self.redirect(str(url))

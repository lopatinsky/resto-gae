from webapp2 import RequestHandler


class IikoBizAppHandler(RequestHandler):
    def get(self):
        self.response.content_type = "text/plain"
        self.response.write("""Hello world!
This is a stub for iiko.biz integration page.
Request params is %s""" % (self.request.params,))

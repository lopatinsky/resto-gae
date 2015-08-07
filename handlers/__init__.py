from google.appengine.api.app_identity import app_identity
from google.appengine.api.urlfetch import DeadlineExceededError
import sys
from methods.email.admin import send_error

__author__ = 'dvpermyakov'

_APP_ID = app_identity.get_application_id()


def handle_500(request, response, exception):
    body = """URL: %s
User-Agent: %s
Exception: %s
Logs: https://appengine.google.com/logs?app_id=s~%s&severity_level_override=0&severity_level=3""" \
           % (request.url, request.headers['User-Agent'], exception, _APP_ID)
    if isinstance(exception, DeadlineExceededError) and ":9900/" in exception.message:
        send_error("iiko", "iiko deadline", body)
    else:
        send_error("server", "Error 500", body)

    exc_info = sys.exc_info()
    raise exc_info[0], exc_info[1], exc_info[2]
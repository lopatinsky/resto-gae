from google.appengine.api import app_identity, mail
from config import config

_EMAIL_DOMAIN = "%s.appspotmail.com" % app_identity.get_application_id()
_DEFAULT_EMAIL = "mdburshteyn@gmail.com"


def send_error(scope, subject, body, html=None):
    subject = "[Resto] " + subject
    if config.DEBUG:
        subject = "[Test]" + subject
    sender = "%s_errors@%s" % (scope, _EMAIL_DOMAIN)
    recipients = config.ERROR_EMAILS.get(scope, _DEFAULT_EMAIL)
    kw = {'html': html} if html else {}
    if recipients == "admins":
        mail.send_mail_to_admins(sender, subject, body, **kw)
    else:
        try:
            mail.send_mail(sender, recipients, subject, body, **kw)
        except:
            pass

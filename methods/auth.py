__author__ = 'dvpermyakov'


def push_admin_user_required(handler):
    def check_user(self, *args, **kwargs):
        if self.user is None:
            self.redirect_to('push_admin_login')
        else:
            return handler(self, *args, **kwargs)
    return check_user
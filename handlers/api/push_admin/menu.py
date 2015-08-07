from methods.auth import push_admin_user_required
from methods.iiko.menu import get_menu

__author__ = 'dvpermyakov'

from base import BaseHandler


class ReloadMenuHandler(BaseHandler):
    @push_admin_user_required
    def get(self):
        get_menu(self.user.company.get().iiko_org_id, force_reload=True)
        self.redirect('/api/push_admin/history?menu_reload')
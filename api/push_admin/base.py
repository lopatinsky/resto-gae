__author__ = 'dvpermyakov'

from webapp2 import RequestHandler, cached_property
from webapp2_extras import auth, sessions, jinja2


class BaseHandler(RequestHandler):
    @cached_property
    def session_store(self):
        return sessions.get_store(request=self.request)

    @cached_property
    def session(self):
        return self.session_store.get_session()

    @cached_property
    def auth(self):
        return auth.get_auth(request=self.request)

    @cached_property
    def user(self):
        user_dict = self.auth.get_user_by_session()
        if user_dict is None:
            return None
        return self.auth.store.user_model.get_by_id(user_dict["user_id"])

    def dispatch(self):
        try:
            super(BaseHandler, self).dispatch()
        finally:
            self.session_store.save_sessions(self.response)

    @cached_property
    def jinja2(self):
        return jinja2.get_jinja2(app=self.app)

    def render(self, template_name, **values):
        values.update(admin=self.user)
        rendered = self.jinja2.render_template(template_name, **values)
        self.response.write(rendered)
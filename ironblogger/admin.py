from flask.ext.admin.contrib.sqla import ModelView
from flask.ext import login
from .app import admin

from . import model
from .currency import format_usd


class AdminViewMixin(object):
    """A mixin class which restricts access to admin users."""

    def is_accessible(self):
        return login.current_user.is_authenticated and login.current_user.is_admin


class AdminModelView(AdminViewMixin, ModelView):
    pass


class UserView(AdminModelView):

    column_list = ('name', 'is_admin')


class BloggerView(AdminModelView):

    form_create_rules = ('name', 'start_date')

class BlogView(AdminModelView):

    column_list = ('blogger', 'title', 'page_url', 'feed_url')
    form_create_rules = ('blogger', 'title', 'page_url', 'feed_url')


class PaymentView(AdminModelView):

    column_formatters = {
        'amount': lambda v,c,m,n: format_usd(m.amount),
    }


class PartyView(AdminModelView):

    column_formatters = {
        'spent': lambda v,c,m,n: format_usd(m.spent),
    }


admin.add_view(UserView(model.User, model.db.session))
admin.add_view(BloggerView(model.Blogger, model.db.session))
admin.add_view(BlogView(model.Blog, model.db.session))
admin.add_view(PaymentView(model.Payment, model.db.session))
admin.add_view(PartyView(model.Party, model.db.session))

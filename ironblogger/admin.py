from flask.ext.admin import Admin, BaseView, expose
from flask.ext.admin.contrib.sqla import ModelView
from flask.ext import login
from ironblogger import model

class AdminViewMixin(object):
    """A mixin class which restricts access to admin users."""

    def is_accessible(self):
        return login.current_user.is_authenticated() and login.current_user.is_admin


class AdminModelView(AdminViewMixin, ModelView):
    pass


class UserView(AdminModelView):

    column_list = ('name', 'is_admin')


class PaymentView(AdminModelView):

    column_formatters = {
        'amount': lambda v,c,m,n: '$%d.%02d' % (m.amount / 100, m.amount % 100)
    }


admin = Admin()
admin.add_view(UserView(model.User, model.db.session))
admin.add_view(PaymentView(model.Payment, model.db.session))

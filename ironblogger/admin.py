from flask.ext.admin import Admin, BaseView, expose

class MainView(BaseView):

    @expose('/')
    def index(self):
        return self.render('admin-test.html')

admin = Admin()
admin.add_view(MainView(name='test'))

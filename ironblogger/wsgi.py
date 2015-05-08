from ironblogger import config
from ironblogger.app import app as application
from ironblogger.model import db as _db
from ironblogger import route as _route
from ironblogger.admin import admin as _admin


def setup(cfg):
    config.setup(cfg)
    application.config['SQLALCHEMY_DATABASE_URI'] = config.cfg['db_uri']
    application.secret_key = config.cfg['app_secret_key']
    _db.init_app(application)
    _admin.init_app(application)

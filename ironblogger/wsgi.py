from ironblogger import config
from ironblogger.app import app as application
from ironblogger.model import db as _db
from ironblogger import route as _route


def setup(cfg):
    config.setup(cfg)
    application.config['SQLALCHEMY_DATABASE_URI'] = config.cfg['db_uri']
    _db.init_app(application)

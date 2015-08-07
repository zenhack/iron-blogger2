from . import config
from .app import app as application
from .model import db as _db
from . import route as _route
from .admin import admin as _admin

_setup_already = False

def setup(cfg):
    config.setup(cfg)
    application.config['SQLALCHEMY_DATABASE_URI'] = config.cfg['db_uri']
    application.secret_key = config.cfg['app_secret_key']
    _db.init_app(application)
    global _setup_already
    if not _setup_already:
        _admin.init_app(application)
        # Flask admin seems to really disklike being initialized twice,
        # as sometimes happens in the test suite.
        _setup_already = True

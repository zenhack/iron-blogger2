from .app import app as application
from .mail import mail as _mail
from .model import db as _db
from . import view as _view
from .admin import admin as _admin

_setup_already = False


def init_app():
    _db.init_app(application)
    _mail.init_app(application)
    global _setup_already
    if not _setup_already:
        _admin.init_app(application)
        # Flask admin seems to really disklike being initialized twice,
        # as sometimes happens in the test suite.
        _setup_already = True

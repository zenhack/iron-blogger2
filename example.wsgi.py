#!/usr/bin/env python
from ironblogger.wsgi import *


# Example config; tune to taste.
application.config.update(
    IB2_REGION='Boston',
    IB2_TIMEZONE='US/Eastern',
    IB2_LANGUAGE='en-us',

    # By default iron blogger will redirect requests for the login page to
    # HTTPS. If you're running a local development server, you may want to turn
    # this off:
    # IB2_FORCE_HTTPS_LOGIN=False,

    # The database to use. Any SQLAlchemy URI can be used, but only SQLite and
    # postgresql have tested, and other DBMSes may not work:
    SQLALCHEMY_DATABASE_URI='sqlite:///' + os.getenv('PWD') + '/ib2.db',
    # Secret key used for things like storing session information.
    # You can generate a key by running:
    #   dd if=/dev/random bs=1 count=128 | base64
    # SECRET_KEY='CHANGEME',

    # How to format timestamps. This should be a format string as described by
    # strftime(3). These both default to "%c", which does something sensible
    # for the locale, but you'll probably want to override them with something
    # nicer. Here's a good example for US English (Used on the Boston site):
    # IB2_TIMESTAMP_LONG="%A %B %d, %Y at %I:%M %P",
    # IB2_TIMESTAMP_SHORT="%a %b %d, %I:%M %P",
)

init_app()

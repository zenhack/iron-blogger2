#!/usr/bin/env python
from ironblogger.wsgi import *


# Example config; tune to taste.
application.config.update(
    IB2_REGION='Boston',
    IB2_TIMEZONE='US/Eastern',
    IB2_LANGUAGE='en-us',
    # The database to use. Any SQLAlchemy URI can be used, but only SQLite and
    # postgresql have tested, and other DBMSes may not work:
    SQLALCHEMY_DATABASE_URI='sqlite:///' + os.getenv('PWD') + '/ib2.db',
    # Secret key used for things like storing session information.
    # You can generate a key by running:
    #   dd if=/dev/random bs=1 count=128 | base64
    # SECRET_KEY='CHANGEME',
)

init_app()

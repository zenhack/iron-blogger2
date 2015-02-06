#!/usr/bin/env python
from ironblogger.wsgi import *

# Example config; tune to taste.
setup({
    'region': 'Boston',
    'timezone': '-0500',
    'language': 'en-us',
    # The database to use. Any SQLAlchemy URI can be used, but only SQLite and
    # postgresql have tested, and other DBMSes may not work:
    'db_uri': 'sqlite:////path/to/sql.db',
})

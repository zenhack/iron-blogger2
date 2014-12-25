#!/usr/bin/env python
from iron_blogger2.config import setup
from iron_blogger2.app import app as application

# Example config; tune to taste.
setup({
    # The database to use. Any SQLAlchemy URI can be used, but only SQLite has
    # been tested, and other DBMSes may not work:
    'db_uri': 'sqlite:////path/to/sql.db',
})

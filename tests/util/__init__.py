"""This package provides helpers for use in tests.

In addition to the contents of the root module, there are three other
modules in this package:

    * randomize - helpers for randomize testing
    * example_data - example data for use in tests
    * feed - helpers for working with feeds
"""
from ironblogger.app import app, db

# The wsgi module centralizes any side-effecting module imports necessary for
# the operation of the app. We import it here for these side effects, and use
# it in a noop statement below to silence the unused import warnings.
import ironblogger.wsgi
ironblogger.wsgi


def fresh_context():
    """yield fixture; runs test with a basic app.config and empty db."""
    app.config.update(
        IB2_REGION='Boston',
        IB2_TIMEZONE='US/Eastern',
        IB2_LANGUAGE='en-us',
        SQLALCHEMY_DATABASE_URI='sqlite:///:memory:',
        SECRET_KEY='CHANGEME',
    )
    with app.test_request_context():
        db.create_all()
        yield
        db.drop_all()

"""This package provides helpers for use in tests.

In addition to the contents of the root module, there are two other
modules in this package:

    * randomize, which provides helpers for randomize testing
    * example_data, which provides example data for use in tests.
"""
from ironblogger.app import app, db
from ironblogger.model import Blogger, Blog
from datetime import datetime
import tempfile
import os

# The wsgi module centralizes any side-effecting module imports necessary for
# the operation of the app. We import it here for these side effects, and use
# it in a noop statement below to silence the unused import warnings.
import ironblogger.wsgi
ironblogger.wsgi


def fresh_context():
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


def feedtext_to_blog(feedtext):
    """Convert the text of a feed to a blog object."""
    with tempfile.NamedTemporaryFile(delete=False) as f:
        name = f.name
        f.write(feedtext)
    try:
        blogger = Blogger(name='Mr. Badguy', start_date=datetime(1973, 3, 17))
        return Blog(
            title='Test Blog',
            page_url='http://www.example.com/blog',
            feed_url=name,
            blogger=blogger
        )
    except Exception:
        # We *don't* want to remove the file if this succeeds; it will probably
        # be used by the tests.
        os.remove(name)
        raise

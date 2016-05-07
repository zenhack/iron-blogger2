from __future__ import unicode_literals
from ironblogger.app import db
from ironblogger.tasks import import_bloggers, export_bloggers
from ironblogger.model import Blogger
from cStringIO import StringIO
from datetime import datetime
from random import Random
from tests.util import fresh_context
from pprint import pformat
from .util.example_data import databases as example_databases
from .util.randomize import random_database
import arrow
import pytest
import json
import difflib

fresh_context = pytest.yield_fixture(autouse=True)(fresh_context)

legacy_yaml = """
alice:
    links:
        - [Fun With Crypto, "http://example.com/alice/blog.html", "http://example.com/alice/rss.xml"]
    start: 2015-04-01
bob:
    links:
        - [Secret Messages, "http://example.com/bob/secrets/blog.html", "http://example.com/bob/secrets/feed"]
        - [Kittens, "http://example.com/bob/kittens", "http://example.com/bob/kittens/feed.atom"]
    start: 2015-04-08
"""


def test_import_bloggers():
    """Import `legacy_yaml` and verify the database contents."""
    import_bloggers(StringIO(legacy_yaml))
    bloggers = Blogger.query.order_by(Blogger.name).all()

    actual = [
        {
            'display_name': blogger.name,
            'start_date': blogger.start_date,
            'blogs': sorted([  # We sort to get a deterministic ordering.
                {
                    'title': blog.title,
                    'page_url': blog.page_url,
                    'feed_url': blog.feed_url,
                } for blog in blogger.blogs
            ]),
        } for blogger in bloggers
    ]

    expected = [
        {
            'display_name': 'alice',
            # Hour is off from midnight, since we're parsing this as EDT.
            'start_date': datetime(2015, 4, 1, 4, 0),
            'blogs': [
                {
                    'title': 'Fun With Crypto',
                    'page_url': 'http://example.com/alice/blog.html',
                    'feed_url': 'http://example.com/alice/rss.xml',
                },
            ],
        },
        {
            'display_name': 'bob',
            'start_date': datetime(2015, 4, 8, 4, 0),
            'blogs': sorted([
                {
                    'title': 'Secret Messages',
                    'page_url': 'http://example.com/bob/secrets/blog.html',
                    'feed_url': 'http://example.com/bob/secrets/feed',
                },
                {
                    'title': 'Kittens',
                    'page_url': 'http://example.com/bob/kittens',
                    'feed_url': 'http://example.com/bob/kittens/feed.atom',
                },
            ])
        },
    ]

    diff = difflib.ndiff(pformat(actual).split('\n'),
                         pformat(expected).split('\n'))
    assert actual == expected, \
        "Import differs from expected result: %s" % pformat(list(diff))


def export_import_export():
    out = StringIO()
    export_bloggers(out)
    out = out.getvalue()
    db.drop_all()
    db.create_all()
    import_bloggers(StringIO(out))
    out2 = StringIO()
    export_bloggers(out2)
    assert json.loads(out) == json.loads(out2.getvalue()), \
        "export(import(export())) != export()"


class Test_export_import_export(object):

    @pytest.mark.parametrize('database', example_databases)
    def test_example_db(self, database):
        db.session.add(database())
        db.session.commit()
        export_import_export()

    @pytest.mark.randomize(seed=int)
    def test_random_db(self, seed):
        random_database(Random(seed), arrow.now())
        export_import_export()

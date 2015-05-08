from ironblogger.app import app
from ironblogger.tasks import import_bloggers
from cStringIO import StringIO
import pytest
from tests.util import fresh_context

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
    # Thus far, the only thing we're really checking is that this doesn't blow up:
    import_bloggers(StringIO(legacy_yaml))

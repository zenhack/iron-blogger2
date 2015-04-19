from ironblogger.app import app
from ironblogger.wsgi import setup
from ironblogger.tasks import import_bloggers
from cStringIO import StringIO

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


with app.test_request_context():
    setup({
        'region'  : 'Boston',
        'timezone': '-0500',
        'language': 'en-us',
        'db_uri'  : 'sqlite:///:memory:',
    })
    # Thus far, the only thing we're really checking is that this doesn't blow up:
    import_bloggers(StringIO(legacy_yaml))

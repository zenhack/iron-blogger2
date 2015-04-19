
from datetime import datetime

from ironblogger.model import db, Blogger, Blog
from ironblogger.app import app
from ironblogger.wsgi import setup
from ironblogger import tasks


with app.test_request_context():
    setup({
        'region'  : 'Boston',
        'timezone': '-0500',
        'language': 'en-us',
        'db_uri'  : 'sqlite:///:memory:',
    })
    db.create_all()

    alice = Blogger(name='Alice',
                    start_date=datetime(2015, 4, 1),
                    blogs=[
                        Blog(title='Fun with crypto',
                             page_url='http://example.com/alice/blog.html',
                             feed_url='http://example.com/alice/rss.xml',
                            )])
    db.session.add(alice)

    alice.create_rounds(datetime(2015, 4, 28))
    assert len(alice.rounds) == 5
    #import pdb; pdb.set_trace()
    alice.create_rounds(datetime(2015, 5, 15))
    assert len(alice.rounds) == 7


    bob = Blogger(name='Bob',
                  start_date=datetime(2015, 4, 8),
                  blogs=[
                      Blog(title='Secret messages',
                           page_url='http://example.com/bob/blog.html',
                           feed_url='http://example.com/bob/rss.xml',
                           )])
    db.session.add(bob)

    tasks.create_rounds(datetime(2015, 5, 15))
    assert len(alice.rounds) == 7
    assert len(bob.rounds) == 6

    # Make sure create_rounds is idempotent:
    tasks.create_rounds(datetime(2015, 5, 15))
    assert len(alice.rounds) == 7
    assert len(bob.rounds) == 6


    # The default arg is meant/useful for testing, but let's at least make sure
    # it doesn't blow up if we don't supply it:
    tasks.create_rounds()
    bob.create_rounds()
    alice.create_rounds()

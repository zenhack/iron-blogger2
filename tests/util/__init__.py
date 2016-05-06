from ironblogger.app import app
from ironblogger.model import db, Blogger, Blog, Post
from ironblogger.date import to_dbtime
from datetime import datetime
from random import Random
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


def random_database(seed, now):
    """Generate a random database based on random seed `seed`.

    This expects to be run within an application context; after the call the
    objects will be stored in the associated datbase.

    Note that this function does not commit the changes to the database; the
    caller must do that themselves.
    """
    rand = Random(seed)

    blogger_choices = ['Alice', 'Bob', 'Cindy', 'Dave', 'Eve', 'Fred', 'Gina',
                       'Henry', 'Isabelle', 'Joe', 'Kate', 'Larry', 'Mallory',
                       'Nina', 'Owen', 'Patty', 'Quentin', 'Ron', 'Sarah',
                       'Tim', 'Uwe', 'Vincent', 'Wendy', 'Xavier', 'Yolanda',
                       'Zack']

    num_bloggers = rand.randint(0, len(blogger_choices) - 1)
    blogger_names = rand.sample(blogger_choices, num_bloggers)

    first_start_date = now.replace(weeks=-8)
    last_start_date = now.replace(weeks=+8)
    for name in blogger_names:
        start_date = random_arrow(rand, first_start_date, last_start_date)
        db.session.add(Blogger(name=name,
                               start_date=to_dbtime(start_date)))


def random_arrow(rand, start, end):
    """Generate a random arrow object in the range [start,end].

    `rand` is an instance of `Random`.
    """
    offset = rand.randint(0, (end - start).total_seconds())
    return start.replace(seconds=offset)


# Example databases; often useful. If we re-use existing objects the tests may
# interfere with one another. By wrapping each of these in a lambda, we ensure
# that a fresh copy is used each time.
example_databases = [
    lambda: Blogger(name='Alice',
                    start_date=datetime(2015, 4, 1),
                    blogs=[
                        Blog(title='Fun with crypto',
                            page_url='http://example.com/alice/blog.html',
                            feed_url='http://example.com/alice/rss.xml',
                            posts=[
                                Post(timestamp=datetime(2015, 4, 1),
                                    title="BREAKING: P = NP; Asymmetric crypto broken forever :(",
                                    summary="The title says it all. There are many other "
                                            "implications of this, but given the topic of...",
                                    page_url='http://example.com/alice/april-fools-pnp.html',
                                    ),
                                Post(timestamp=datetime(2015, 4, 15),
                                    title="Security Breach",
                                    summary="Sorry I didn't post last week. There was a security "
                                            "breach at work, and I was busy dealing with...",
                                    page_url='http://example.com/alice/security-breach.html',
                                    ),
                                Post(timestamp=datetime(2015, 4, 16),
                                    title="Javascript and timing attacks",
                                    summary="Owing to it being the only thing available in the "
                                            "browser, people are doing more and more with Javascript...",
                                    page_url='http://example.com/alice/javascript-timing-attacks.html',
                                    ),
                                ]
            )]),
    lambda: Blogger(name='bob',
                    start_date=datetime(2015, 4, 1),
                    blogs=[
                        Blog(title='Theoretical piracy',
                            page_url='http://example.com/bob/blog.html',
                            feed_url='http://example.com/bob/blog.atom',
                            posts=[
                                Post(title="Rivest admits he doesn't care, about security, just really likes prime numbers.",
                                    summary="""In an interview, Robert Rivest told reporters that "I'm really only into it for the math...""",
                                    page_url='http://example.com/bob/rivest.html',
                                    timestamp=datetime(2015, 4, 1),
                                    ),
                                Post(title="Real world cryptographic hash functions have no theoretical basis, and we're all doomed",
                                    summary="We're using cryptographic hash functions like sha256 as ideal hash functions. Ideal hash "
                                            "functions provably do not exist. This in itself isn't actually that scary, but the really "
                                            "worrysome thing is that we don't even have a well defined notion of what's 'good enough'; "
                                            "What's the approximation that we're actually relying on?",
                                    page_url='http://example.com/bob/hash-functions.html',
                                    timestamp=datetime(2015, 4, 8),
                                    ),
                                Post(title="Timing sidechannels ruin everything, and we have no answers whatsoever ",
                                    summary="There's a known attack on SSH that's been around for 15 years, that allows "
                                            "an attacker to sniff passwords by measuring the timing of a user's keystrokes --- "
                                            "no decryption required. Nobody's done anything about it, and while we have some ideas "
                                            "about how to deal with this one, there's a whole class of attacks out there that we "
                                            "just have no answer for.",
                                    page_url='http://example.com/bob/timing-sidechannels.html',
                                    timestamp=datetime(2015, 4, 9),
                                    ),
                                Post(title="I've realized I'm suffering from depression.",
                                    summary="You may have noticed my past few posts were especially dark...",
                                    page_url='http://example.com/bob/depressed.html',
                                    timestamp=datetime(2015, 4, 15),
                                    ),
                            ]
            )]),
]

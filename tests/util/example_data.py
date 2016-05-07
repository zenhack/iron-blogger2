"""This module provides example data to use in tests.

Right now this contains:
* the variable `databases`, which i a list of callables, each of which takes
  no arguments and returns an object which may be added to the database with
  `db.session.add`. Doing so will pull in the rest of the sample database's
  objects via dependency.
* the variables malcious_posts, malformed_posts, and good_posts, each of
  which is a list of dictionaries of the form::

    {
        'title': <Post title>,
        'link': <link to post>,
        'pubDate': <date, as a string>,
        'description': <description/summary of the post>,
    },

  ...the fields being named for their element names in RSS. As the name
  implies, malformed_posts contains some values which aren't actually valid
  (e.g. badly formatted dates).

NOTE WELL: some of the tests depend on specific knowledge of the details of
these values, so they should not be changed willy-nilly.
"""
from ironblogger.model import Blogger, Blog, Post
from datetime import datetime

# If we re-use existing objects the tests may interfere with one another. By
# wrapping each of these in a lambda, we ensure that a fresh copy is used each time.
#
# TODO: we ought to convert this to a dict with memorable keys that describe
# the contents, or something similar.
databases = [
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


def _format_date(date_obj):
    """This is basically rssdate, but with a hard-coded timezone.

    rssdate gets the timezone from flask's config, which won't be available
    at import time, so we use this in the datasets below.
    """
    return date_obj.strftime('%d %b %Y %T -0500')


malicious_posts = [
    {'title': 'script in summary',
     'link': 'script-in-summary.html',
     'pubDate': _format_date(datetime(2014, 12, 26)),
     'description': '''
        <script>doBadThings();</script>
        <p>mwahahaha</p>
     '''},
]

malformed_posts = [
    {
        'title': 'Post with bad date',
        'link': 'post-with-bad-date.html',
        'pubDate': 'never',
        'description': "Hello, World!\n",
    },
    {
        'title': 'mwahahaha',
        'link': 'mwhahahah.html',
        'pubDate': "You'll never sync the rest of the posts!",
        'description': '''
        You'll never sync the rest of the posts, because when
        fetch_posts tries to parse the date in this one, you'll get a
        MalformedPostError, and not sync the rest of the blogs!

        Mwhahahaha!
        ''',
    },
]

good_posts = [
    {
        'title': 'Diffie-Hellman FTW.',
        'link': 'diffe-hellman.html',
        'pubDate': _format_date(datetime(1976, 12, 4)),
        'description': 'Neat paper that just came out...',
    },
    {'title': 'Perfect forward secrecy is pretty cool.',
        'link': 'perfect-forward-secrecy.html',
        'pubDate': _format_date(datetime(2014, 12, 30)),
        'description': '''
        OTR does a good job with this. Too bad it's hard to do with
        something like email, where there's no "session."
        ''',
    }
]

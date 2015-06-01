from datetime import datetime
import unittest
import pytest
from tests.util import fresh_context

from ironblogger.model import db, Blogger, Blog, Post
from ironblogger.app import app
from ironblogger.date import duedate
from ironblogger import tasks

fresh_context = pytest.yield_fixture(autouse=True)(fresh_context)


class Test_assign_rounds(unittest.TestCase):

    def _get_week(self, when):
        return db.session.query(Post)\
            .filter_by(counts_for=duedate(when)).first()

    def verify_assignment(self, when, title_part, late):
        post = self._get_week(when)
        assert title_part in post.title
        assert post.rounds_late() == late

    def test_01(self):
        # During a 5-week period, alice:
        #
        # * Posts on time in the first week
        # * Misses week 2
        # * Posts twice in week 3
        # * Misses weeks 4 and 5
        alice = Blogger(name='Alice',
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
                                        page_url='http:///example.com/alice/javascript-timing-attacks.html',
                                        ),
                                    ]
                                )])
        db.session.add(alice)
        end_date = datetime(2015, 4, 28)
        tasks.assign_rounds(until=end_date)
        self.verify_assignment(datetime(2015, 4,  1), "BREAKING:",       0)
        self.verify_assignment(datetime(2015, 4, 15), "Security Breach", 0)
        self.verify_assignment(datetime(2015, 4,  8), "Javascript",      1)
        assert self._get_week(datetime(2015, 4, 22)) is None

        # Just make sure this doesn't explode:
        tasks.assign_rounds()

    def test_02(self):
        # During a 4 week-period, bob:
        #
        # * Posts once in round 1
        # * Twice in round 2
        # * Once in round 3
        # * Misses round 4
        bob = Blogger(name='bob',
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
                      )])
        db.session.add(bob)
        end_date = datetime(2015, 4, 21)
        tasks.assign_rounds(until=end_date)
        self.verify_assignment(datetime(2015, 4,  1), "Rivest",         0)
        self.verify_assignment(datetime(2015, 4,  8), "hash functions", 0)
        self.verify_assignment(datetime(2015, 4, 15), "depression",     0)
        assert self._get_week(datetime(2015, 4, 22)) is None
        extra_post = db.session.query(Post).filter_by(timestamp=datetime(2015, 4, 9)).one()
        assert extra_post.rounds_late() is None

        # Just make sure this doesn't explode:
        tasks.assign_rounds()

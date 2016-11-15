from datetime import datetime
from ironblogger.date import rssdate, from_dbtime
from ironblogger import tasks
from ironblogger.model import *
import os.path
import pytest
from lxml import etree
from six.moves import StringIO

from tests.util import fresh_context

from tests.util.example_data import \
    malicious_posts, malformed_posts, good_posts
from tests.util.feed import rss_feed_template, atom_feed_template, \
    feedtext_to_blog


fresh_context = pytest.yield_fixture(autouse=True)(fresh_context)


def post_summary_etree(post):
    summary = StringIO('<section>%s</section>' % post.summary)
    parser = etree.HTMLParser()
    return etree.parse(summary, parser)


@pytest.mark.parametrize('post', malformed_posts)
def test_malformed(post):
    blog = feedtext_to_blog(rss_feed_template.render(items=[post]))
    try:
        with pytest.raises(MalformedPostError):
            blog.fetch_posts()
    finally:
        os.remove(blog.feed_url)


@pytest.mark.parametrize('post', malicious_posts)
def test_malicious(post):
    blog = feedtext_to_blog(rss_feed_template.render(items=[post]))
    try:
        blog.fetch_posts()
        tree = post_summary_etree(blog.posts[0])
        assert len(tree.getroot().findall('.//p')) == 1
        assert len(tree.getroot().findall('.//script')) == 0
    finally:
        os.remove(blog.feed_url)


def test_interrupt_sync():
    """A malformed post in one blog should not prevent syncing the rest.

    This test tries to sync all the blogs, one of which has a post with an
    invalid publication date. The others blogs should still have their posts
    collected, and the bad post should not find its way into the db.
    """
    blogs = {
        'alice': [good_posts[0]],
        'mallory': [malformed_posts[1]],
        'bob': [good_posts[1]],
    }
    for blogger_name in 'alice', 'mallory', 'bob':
        blog = feedtext_to_blog(rss_feed_template.render(items=blogs[blogger_name]))
        blog.blogger = Blogger(name=blogger_name, start_date=datetime(1949, 10, 31))
        blogs[blogger_name] = blog
        db.session.add(blog)

    tasks.fetch_posts()
    assert len(blogs['alice'].posts) == 1
    assert len(blogs['mallory'].posts) == 0
    assert len(blogs['bob'].posts) == 1

    # clean up the temporary files:
    for _, blog in blogs.iteritems():
        os.remove(blog.feed_url)


def test_text_mimetype():
    """Test that entries with mime type "text/plain" are properly escaped.

    Feedparser doesn't do this automatically, so we have to check it ourselves.
    """
    pubdate = rssdate(from_dbtime(datetime(2014, 12, 31)))
    entry = '''
    <title>Texsploit</title>
    <link>/all/your/base</link>
    <id>urn:uuid:5d181038-9f58-4f59-ac6d-06a6f42f5ae7</id>
    <updated>%s</updated>
    <published>%s</published>
    <summary type="text/plain" mode="escaped">
        &lt;script&gt;allYourBase();&lt;/script&gt;
        &lt;p&gt;mwahahaha&lt;/p&gt;
    </summary>
    ''' % (pubdate, pubdate)
    blog = feedtext_to_blog(atom_feed_template.render(entries=[entry]))

    # Double check that the mime type -- the whole point of this test is plain
    # text.
    feed = feedparser.parse(blog.feed_url)
    assert feed.entries[0].summary_detail.type == 'text/plain'

    try:
        blog.fetch_posts()
        summary = post_summary_etree(blog.posts[0])
        assert len(summary.getroot().findall('.//script')) == 0
    finally:
        os.remove(blog.feed_url)

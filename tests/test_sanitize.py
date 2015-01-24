from datetime import date
from ironblogger.config import setup as app_setup
from ironblogger import cli
from ironblogger.app import app
from ironblogger.model import *
import os.path
import pytest
import tempfile
from lxml import etree
from StringIO import StringIO

from jinja2 import Template

from tests.util import fresh_context


rss_feed_template = '''
<?xml version="1.0" encoding="utf-8"?>
<rss version="2.0">
    <channel>
        <title>Blackhat posts</title>
        <link>index.html</link>
        <description>Posts that will exploit your app</description>
        <language>en-us</language>

        {% for item in items %}
        <item>
            <title>{{ item['title'] }}</title>
            <link>{{ item['link'] }}</link>
            <pubDate>{{ item['pubDate'] }}</pubDate>
            <description>
            {{ item['description'] }}
            </description>
        </item>
        {% endfor %}
    </channel>
</rss>
'''

atom_feed_template = '''
<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
    <title>Blackhat posts</title>
    <link>index.html</link>
    <updated>2015-01-01T2030:02Z</updated>
    <author>
      <name>Mr. Badguy</name>
    </author>
    <id>urn:uuid:ff34221c-6624-42da-86a3-d512537170d1</id>
    {% for entry in entries %}
    <entry>
        {{ entry }}
    </entry>
    {% endfor %}
</feed>
'''

rss_feed_template = Template(rss_feed_template, autoescape=False)
atom_feed_template = Template(atom_feed_template, autoescape=False)


def _format_date(d):
    # We want to return a timestamp with a timezone, but '%z' on a date
    # object will return the empty string, so we just hardcode an arbitrary
    # value, in this caes GMT -5 (EST).
    return d.strftime('%F %T') + ' -0500'


malicious_posts = [
    {'title': 'script in summary',
     'link': 'script-in-summary.html',
     'pubDate': _format_date(date(2014, 12, 26)),
     'description': '''
        <script>doBadThings();</script>
        <p>mwahahaha</p>
     '''},
]

malformed_posts = [
    {'title': 'Post with bad date',
     'link': 'post-with-bad-date.html',
     'pubDate': 'never',
     'description': "Hello, World!\n",
     },
]


def as_file(data):
    with tempfile.NamedTemporaryFile(delete=False) as f:
        name = f.name
        f.write(data)
    return name

def to_blog(feedtext):
    with tempfile.NamedTemporaryFile(delete=False) as f:
        name = f.name
        f.write(feedtext)
    try:
        blogger = Blogger('Mr. Badguy', date(1973, 3, 17))
        return Blog(
                title='Test Blog',
                page_url='http://www.example.com/blog',
                feed_url=name,
                blogger=blogger)
    except Exception:
        os.remove(name)
        raise


def post_summary_etree(post):
    summary = StringIO('<section>%s</section>' % post.summary)
    parser = etree.HTMLParser()
    return etree.parse(summary, parser)


fresh_context = pytest.yield_fixture(autouse=True)(fresh_context)


@pytest.mark.parametrize('post', malformed_posts)
def test_malformed(post):
    blog = to_blog(rss_feed_template.render(items=[post]))
    try:
        with pytest.raises(MalformedPostError):
            blog.sync_posts()
    finally:
        os.remove(blog.feed_url)


@pytest.mark.parametrize('post', malicious_posts)
def test_malicious(post):
    blog = to_blog(rss_feed_template.render(items=[post]))
    try:
        blog.sync_posts()
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
            'alice': [
                {'title': 'Diffie-Hellman FTW.',
                 'link': 'diffe-hellman.html',
                 'pubDate': _format_date(date(1976, 12, 4)),
                 'description': 'Neat paper that just came out...',
                 },
            ],
            'mallory': [
                {'title': 'mwahahaha',
                 'link': 'mwhahahah.html',
                 'pubDate': "You'll never sync the rest of the posts!",
                 'description': '''
                   You'll never sync the rest of the posts, because when
                   sync_posts tries to parse the date in this one, you'll get a
                   MalformedPostError, and not sync the rest of the blogs!

                   Mwhahahaha!
                 ''',
                },
            ],
            'bob': [
                {'title': 'Perfect forward secrecy is pretty cool.',
                 'link': 'perfect-forward-secrecy.html',
                 'pubDate': _format_date(date(2014, 12, 30)),
                 'description': '''
                   OTR does a good job with this. Too bad it's hard to do with
                   something like email, where there's no "session."
                 ''',
                }
            ],
    }
    for blogger_name in 'alice', 'mallory', 'bob':
        blog = to_blog(rss_feed_template.render(items=blogs[blogger_name]))
        blog.blogger = Blogger(blogger_name, date(1949, 10, 31))
        blogs[blogger_name] = blog
        db.session.add(blog)

    cli.sync_posts()
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
    pubdate = _format_date(date(2014, 12, 31))
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
    blog = to_blog(atom_feed_template.render(entries=[entry]))

    # Double check that the mime type -- the whole point of this test is plain
    # text.
    feed = feedparser.parse(blog.feed_url)
    assert feed.entries[0].summary_detail.type == 'text/plain'

    try:
        blog.sync_posts()
        summary = post_summary_etree(blog.posts[0])
        assert len(summary.getroot().findall('.//script')) == 0
    finally:
        os.remove(blog.feed_url)

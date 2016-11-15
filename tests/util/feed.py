"""This module provides toosl for working atom & rss feeds.

* Jinja 2 templates. For sample data with which to populate them,
  see `example_data`.
* the feedtext_to_blog function
"""

from jinja2 import Template
from ironblogger.model import Blog, Blogger
from datetime import datetime
import tempfile
import os

rss_feed_template = \
'''<?xml version="1.0" encoding="utf-8"?>
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

atom_feed_template = \
'''<?xml version="1.0" encoding="utf-8"?>
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


def feedtext_to_blog(feedtext):
    """Convert the text of a feed to a blog object."""
    with tempfile.NamedTemporaryFile(delete=False) as f:
        name = f.name
        f.write(feedtext.encode('utf-8'))
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

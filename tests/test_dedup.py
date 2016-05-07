"""Test de-duplication of modified posts.

Sometimes various attributes of a post changes in the feed after it's been
published. We try to detect this and not create a second entry for it.
"""

import pytest
from jinja2 import Template
from .util import fresh_context
from .util.feed import feedtext_to_blog
from ironblogger.model import db, Post

fresh_context = pytest.yield_fixture(autouse=True)(fresh_context)

feed_template = Template("""
<?xml version="1.0" encoding="utf-8"?>
<rss version="2.0">
    <channel>
        <title>Tentative Blog Posts</title>
        <link>index.html</link>
        <description>Blog posts by someone with commitment issues.</description>
        <language>en-us</language>

        <item>
            <title>{{ title }}</title>
            <link>{{ link }}</link>
            <pubDate>{{ pubDate }}</pubDate>
            {% if guid %}
            <guid>{{ guid }}</guid>
            {% endif %}
            <description>
                I keep changing the metadata on my posts; it's
                really getting to be a problem but I don't know
                how to just stick to something...
            </description>
        </item>
    </channel>
</rss>
""".strip(), autoescape=False)

original_post = {
    'title': 'Obsessing About Metadata',
    'link': 'https://example.com/blog/posts/metadata.html',
    'pubDate': '15 Apr 2016 00:00:00 -0400',
    'guid': '1',
}

changes = {
    'title': 'Obsessing Over Metadata',
    'link': 'https://example.com/blog/posts/obsessing.html',
    'pubDate': '15 Apr 2016 00:30:00 -0400',
    'guid': '2',
}


@pytest.mark.parametrize('to_keep', ['title', 'link', 'guid'])
def test_detect_change(to_keep):
    blog = feedtext_to_blog(feed_template.render(**original_post))
    db.session.add(blog)
    blog.fetch_posts()
    assert Post.query.count() == 1, "Wrong number of posts on initial import"

    new_post = original_post.copy()
    for key in changes.keys():
        if key != to_keep:
            new_post[key] = changes[key]
    with open(blog.feed_url, 'w') as f:
        f.write(feed_template.render(**new_post))
    blog.fetch_posts()
    assert Post.query.count() == 1, "Post dedup failed"


def test_no_dedup_new():
    blog = feedtext_to_blog(feed_template.render(**original_post))
    db.session.add(blog)
    blog.fetch_posts()
    assert Post.query.count() == 1, "Wrong number of posts on initial import"

    with open(blog.feed_url, 'w') as f:
        f.write(feed_template.render(**changes))
    blog.fetch_posts()
    assert Post.query.count() == 2, "New post was not counted correctly."

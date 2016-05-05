"""Crawl the web interface, making sure pages return correct status codes.

So far, we're only testing pages that we know should always return 200.
"""
import pytest
from lxml import etree
from flask import url_for
from urlparse import urlparse

from ironblogger import tasks
from ironblogger.app import app
from ironblogger.model import db, Post
from .util import fresh_context, example_databases
fresh_context = pytest.yield_fixture(autouse=True)(fresh_context)


@pytest.fixture
def client():
    return app.test_client()


def test_root(client):
    resp = client.get('/')
    # / should redirect us to /posts
    assert resp.status_code == 302


def test_login(client):
    # /login should redirect to https
    resp = client.get('/login')
    assert resp.status_code == 302
    assert resp.headers['Location'][:len('https')] == 'https'
    assert resp.headers['Location'][-len('/login'):] == '/login'

    # accessing via https should work
    resp = client.get('/login', environ_overrides={'wsgi.url_scheme': 'https'})
    assert resp.status_code == 200


# Starting points for crawling the site.
root_pages = (
    '/',
    '/admin/',
)


def test_empty_db_ok(client):
    """Crawl the website with an empty database."""
    assert_no_dead_links(client)


@pytest.mark.parametrize('database', example_databases)
def test_populated_db_page_ok(client, database):
    """Crawl the website with a populated database.

    This tests checks the site both before and after assigning rounds
    to posts.
    """
    db.session.add(database())
    db.session.commit()

    assert_no_dead_links(client)

    last_post = db.session.query(Post.timestamp)\
        .order_by(Post.timestamp.desc())\
        .first()[0]
    tasks.assign_rounds(until=last_post)

    assert_no_dead_links(client)


def is_internal_link(link):
    root_url = urlparse(url_for('show_index', _external=True))
    this_url = urlparse(link)
    return this_url.netloc in ('', root_url.netloc)


def assert_no_dead_links(client, path=None, visited=None):
    if visited is None:
        visited = set()
    if path is None:
        for path in root_pages:
            assert_no_dead_links(client, path, visited)

    if path in visited or not is_internal_link(path):
        # Don't need to visit this one.
        return

    visited.add(path)
    resp = client.get(path)

    assert 200 <= resp.status_code < 400, \
        "Bad status code for page %r: %r" % (path, resp.status_code)

    if resp.status_code >= 300:
        assert_no_dead_links(client, resp.headers['Location'], visited=visited)
    elif 'text/html' not in resp.headers['Content-Type']:
        # No links to follow.
        return
    else:
        parser = etree.HTMLParser()
        html = etree.fromstring(resp.data, parser)
        links = (
            [elt.attrib['href'] for elt in
             html.findall('.//a[@href]') +
             html.findall('.//link[@href]')
             ] +
            [elt.attrib['src'] for elt in
             html.findall('.//img[@src]') +
             html.findall('.//script[@src]')
             ]
        )

        for link in links:
            if is_internal_link(link):
                assert_no_dead_links(client, link, visited)

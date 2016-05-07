"""Crawl the web interface, making sure pages return correct status codes.

So far, we're only testing pages that we know should always return 200.
"""
import pytest
from lxml import etree
from flask import url_for
from urlparse import urlparse
import arrow
from random import Random

from ironblogger import tasks
from ironblogger.app import app
from ironblogger.model import db, Post
from ironblogger.date import to_dbtime
from .util.example_data import databases as example_databases
from .util.randomize import random_database, random_ncalls
from .util import fresh_context
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
def test_empty_db_ok(client):
    """Crawl the website with an empty database."""
    assert_no_dead_links_site(client)


@pytest.mark.parametrize('database', example_databases)
def test_populated_db_page_ok(client, database):
    """Crawl the website with a populated database.

    This tests checks the site both before and after assigning rounds
    to posts.
    """
    db.session.add(database())
    db.session.commit()

    assert_no_dead_links_site(client)

    last_post = db.session.query(Post.timestamp)\
        .order_by(Post.timestamp.desc())\
        .first()[0]
    tasks.assign_rounds(until=last_post)

    assert_no_dead_links_site(client)


@pytest.mark.randomize(seed=int, ncalls=random_ncalls)
def test_random_db_ok(client, seed):
    """Crawl the website with a randomized database.

    This tests checks the site both before and after assigning rounds
    to posts.
    """
    rand = Random(seed)
    now = arrow.now()
    random_database(rand, now)
    db.session.commit()
    assert_no_dead_links_site(client)

    tasks.assign_rounds(until=to_dbtime(now))
    db.session.commit()
    assert_no_dead_links_site(client)

    page_size = rand.randint(1, 100)
    _assert_no_dead_links_page(client,
                               '/?page=1&page_size=%d' % page_size,
                               set())



def is_internal_link(link):
    root_url = urlparse(url_for('show_index', _external=True))
    this_url = urlparse(link)
    return this_url.netloc in ('', root_url.netloc)


def find_all_links(page_text):
    """Return all of the links in `page_text`.

    `page_text` is the text of an html document.

    We reterun the `href` attributes of all `a` and `link` tags, and the `src`
    attributes of all `img` and `script` tags. Additions to this list are
    welcome.
    """
    parser = etree.HTMLParser()
    html = etree.fromstring(page_text, parser)
    return (
        [elt.attrib['href'] for elt in
         html.findall('.//a[@href]') +
         html.findall('.//link[@href]')
         ] +
        [elt.attrib['src'] for elt in
         html.findall('.//img[@src]') +
         html.findall('.//script[@src]')
         ]
    )


def assert_no_dead_links_site(client):
    """Crawl the website looking for dead links, assert their abscence.

    This function uses `client` to crawl the iron blogger website, (both
    the public site and the admin interface). If any internal link it attempts
    to follow returns non-success non-redirect status, this causes a test
    failure.
    """
    visited = set()
    # We need to start the search at *both* the root *and* /admin, because
    # the latter isn't actually reachable from the landing page.
    for start in '/', '/admin/':
        _assert_no_dead_links_page(client, start, visited)


def _assert_no_dead_links_page(client, path, visited):
    """Helper for assert_no_dead_links_site.

    Recursively checks the page at `path`. `visited` is a set of all
    links that have already been followed. If `path` is in `visited` or
    `path` is an external link, it is skipped.
    """
    if path in visited:
        # Already been here; do nothing
        return
    if not is_internal_link(path):
        # This goes outside our website; we don't test for that.
        return

    visited.add(path)
    resp = client.get(path)

    assert 200 <= resp.status_code < 400, \
        "Bad status code for page %r: %r" % (path, resp.status_code)

    if resp.status_code >= 300:
        # Redirect
        _assert_no_dead_links_page(client,
                                   resp.headers['Location'],
                                   visited)
    elif 'text/html' in resp.headers['Content-Type']:
        # We only want to scan the page if it's actually html
        for link in find_all_links(resp.data):
            if is_internal_link(link):
                _assert_no_dead_links_page(client, link, visited)

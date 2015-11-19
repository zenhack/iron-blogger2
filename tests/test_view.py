"""Crawl the web interface, making sure pages return correct status codes.

So far, we're only testing pages that we know should always return 200.
"""
import pytest

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


pages = (
    '/posts',
    '/bloggers',
    '/status',
    '/ledger',
    '/rss',
    '/about',

    # Not on the main nav, but still.
    '/admin/',
)


@pytest.mark.parametrize('page', pages)
def test_empty_db_ok(client, page):
    """Crawl the website with an empty database."""
    resp = client.get(page)
    assert resp.status_code == 200


@pytest.mark.parametrize('page,database', [(p, d)
                                           for p in pages
                                           for d in example_databases])
def test_populated_db_page_ok(client, page, database):
    """Crawl the website with a populated database.

    This tests checks each page both before and after assigning rounds
    to posts.
    """
    db.session.add(database())
    db.session.commit()

    resp = client.get(page)
    assert resp.status_code == 200

    last_post = db.session.query(Post.timestamp)\
        .order_by(Post.timestamp.desc())\
        .first()[0]
    tasks.assign_rounds(until=last_post)
    resp = client.get(page)
    assert resp.status_code == 200

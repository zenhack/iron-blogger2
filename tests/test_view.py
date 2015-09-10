import pytest

from ironblogger.app import app
from ironblogger.model import db
from .util import fresh_context, example_databases
fresh_context = pytest.yield_fixture(autouse=True)(fresh_context)


@pytest.fixture
def client():
    return app.test_client()


def test_root(client):
    resp = client.get('/')
    # / should redirect us to /posts
    assert resp.status_code == 302

pages = (
    '/posts',
    '/bloggers',
    '/status',
    '/ledger',
    '/rss',
    '/about',
    '/login',

    # Not on the main nav, but still.
    '/admin/',
)


@pytest.mark.parametrize('page', pages)
def test_empty_page_ok(client, page):
    """Each of these pages should return successfully."""
    resp = client.get(page)
    assert resp.status_code == 200


@pytest.mark.parametrize('page,database', [(p, d)
                                           for p in pages
                                           for d in example_databases])
def test_db_page_ok(client, page, database):
    db.session.add(database())
    db.session.commit()
    resp = client.get(page)
    assert resp.status_code == 200

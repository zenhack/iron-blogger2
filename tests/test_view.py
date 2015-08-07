import pytest

from ironblogger.app import app
from .util import fresh_context
fresh_context = pytest.yield_fixture(autouse=True)(fresh_context)

@pytest.fixture
def client():
    return app.test_client()


def test_root(client):
    resp = client.get('/')
    # / should redirect us to /posts
    assert resp.status_code == 302

@pytest.mark.parametrize('page', [
    '/posts',
    '/bloggers',
    '/status',
    '/ledger',
    '/rss',
    '/about',

    # Not on the main nav, but still.
    '/admin/',
])
def test_page_ok(client, page):
    """Each of these pages should return successfully."""
    resp = client.get(page)
    assert resp.status_code == 200

from ironblogger import model
from tests.util import fresh_context
from datetime import datetime
import pytest

fresh_context = pytest.yield_fixture(autouse=True)(fresh_context)


def test_passwords():
    alice = model.User(name='alice')
    assert alice.verify_password('secret') is False
    alice.set_password('secret')
    assert alice.verify_password('secret') is True
    assert alice.verify_password('god')    is False


def test_user_id():
    alice = model.User(name='alice')
    assert alice.get_id() == 'alice'


def test_blogger_repr():
    """Verify that the blogger's repr is it's name.

    This is actually used in the UI, and so important."""
    blogger = model.Blogger(name='bob', start_date=datetime.now())
    assert repr(blogger) == 'bob'

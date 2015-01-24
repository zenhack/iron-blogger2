from ironblogger.app import app
from ironblogger.config import setup
from ironblogger.model import db


def fresh_context():
    setup({
        'db_uri': 'sqlite:///:memory:',
    })
    with app.test_request_context():
        db.create_all()
        yield

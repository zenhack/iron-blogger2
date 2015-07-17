from ironblogger.app import app
from ironblogger.wsgi import setup
from ironblogger.model import db


def fresh_context():
    setup({
        'region': 'Boston',
        'timezone': 'US/Eastern',
        'language': 'en-us',
        'db_uri': 'sqlite:///:memory:',
        'app_secret_key': 'CHANGEME',
    })
    with app.test_request_context():
        db.create_all()
        yield

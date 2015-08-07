from ironblogger.app import app
from ironblogger.wsgi import init_app
from ironblogger.model import db


def fresh_context():
    app.config.update(
        IB2_REGION='Boston',
        IB2_TIMEZONE='US/Eastern',
        IB2_LANGUAGE='en-us',
        SQLALCHEMY_DATABASE_URI='sqlite:///:memory:',
        SECRET_KEY='CHANGEME',
    )
    init_app()
    with app.test_request_context():
        db.create_all()
        yield

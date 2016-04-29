"""This module exposes the wsgi application.

It imports all of the modules needed for their side effects e.g.
(populating the URL map), and exposes our flask app under the
wsgi-prescribed name "application." The actual wsgi script can just do:

    from ironblogger.wsgi import *

    application.config.update(
    ...
    )
"""
from .app import app as application
from . import view as _view
from . import model as _model
from . import admin as _admin

# Some tools will complain about the unused imports, so we use them in a dummy
# statement to silence these warnings:
application, _view, _model, _admin

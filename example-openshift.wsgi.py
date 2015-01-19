#!/usr/bin/python
# wsgi script configured to run under redhat's openshift, using postgresql for
# the database.
#
# To use this, copy it to wsgi.py edit, APPNAME (below) if need be, uncomment
# the dependency for postgresql in requirements.txt, commit, and push. you'll
# have to arrange for the initial population of the database yourself. If you
# enable the cron cartridge, the `.openshift`, directory contains a job that
# will sync the posts every hour.

# This bit is copied from openshift's standard python boilerplate:
import os

virtenv = os.environ['OPENSHIFT_PYTHON_DIR'] + '/virtenv/'
virtualenv = os.path.join(virtenv, 'bin/activate_this.py')
try:
    execfile(virtualenv, dict(__file__=virtualenv))
except IOError:
    pass

# Okay, the rest of this is all us, and just standard wsgi.

APPNAME = 'ironblogger' # The name of our app on openshift.

from ironblogger.config import setup
from ironblogger.app import app as application

setup({
    'db_uri': os.getenv('OPENSHIFT_POSTGRESQL_DB_URL') + '/' + APPNAME,
})

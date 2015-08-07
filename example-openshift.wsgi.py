#!/usr/bin/python
# wsgi script configured to run under redhat's openshift, using postgresql for
# the database.
#
# To use this, copy it to wsgi.py edit, APPNAME (below) if need be, uncomment
# the dependency for postgresql in setup.py, generate a secret key as described
# in the comments below (and add it to this file) commit, and push. you'll
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
from ironblogger.wsgi import *


APPNAME = 'ironblogger'  # The name of our app on openshift.
application.config.update(
    IB2_REGION='Boston',
    IB2_TIMEZONE='US/Eastern',
    IB2_LANGUAGE='en-us',
    SQLALCHEMY_DATABASE_URI=os.getenv('OPENSHIFT_POSTGRESQL_DB_URL') + '/' + APPNAME,
    # Secret key used for things like storing session information.
    # You can generate a key by running:
    #   dd if=/dev/random bs=1 count=128 | base64
    # SECRET_KEY='CHANGEME',
)

init_app()

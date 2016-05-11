import pytest
from ironblogger.date import *
from ironblogger.app import app
from datetime import datetime

rssdate_cases = [
    (datetime(2015, 1, 25), 'US/Eastern', '24 Jan 2015 19:00:00 -0500'),
]


@pytest.mark.parametrize('date_obj,zone,output', rssdate_cases)
def test_rssdate_pass_cfg(date_obj, zone, output):
    app.config['IB2_TIMEZONE'] = zone
    assert rssdate(from_dbtime(date_obj)) == output

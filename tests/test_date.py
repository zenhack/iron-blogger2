import pytest
from ironblogger.date import *
from datetime import date

rssdate_cases = [
    (date(2015, 1, 25), {'timezone': 'US/Eastern'}, '24 Jan 2015 19:00:00 -0500'),
]

@pytest.mark.parametrize('date_obj,cfg,output', rssdate_cases)
def test_rssdate_pass_cfg(date_obj, cfg, output):
    assert rssdate(date_obj, cfg) == output

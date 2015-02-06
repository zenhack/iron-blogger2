import pytest
from ironblogger.date import *

rssdate_cases = [
    (date(2015, 1, 25), {'timezone': '-0500'}, '25 Jan 2015 00:00:00 -0500'),
]

@pytest.mark.parametrize('date_obj,cfg,output', rssdate_cases)
def test_rssdate_pass_cfg(date_obj, cfg, output):
    assert rssdate(date_obj, cfg) == output

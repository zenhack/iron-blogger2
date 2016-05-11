
from .app import app
from .date import rssdate, from_dbtime
from .currency import format_usd


format_usd = app.template_filter('currency')(format_usd)


@app.template_filter()
def timestamp_rss(date):
    # XXX: This filter is currently only used on database objects, so we need
    # this to be a dbtime, but it's a bit ugly, since we normally try to avoid
    # doing logic with dbtimes.
    return rssdate(from_dbtime(date))


@app.template_filter()
def timestamp_long(date):
    return date.strftime(app.config['IB2_TIMESTAMP_LONG'])


@app.template_filter()
def timestamp_short(date):
    return date.strftime(app.config['IB2_TIMESTAMP_SHORT'])


@app.template_filter()
def datestamp(date):
    return date.strftime(app.config['IB2_DATESTAMP'])

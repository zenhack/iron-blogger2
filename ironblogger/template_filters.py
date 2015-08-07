
from .app import app
from .date import rssdate
from .currency import format_usd


format_usd = app.template_filter('currency')(format_usd)
rssdate = app.template_filter()(rssdate)


@app.template_filter()
def timestamp_long(date):
    return date.strftime(app.config['IB2_TIMESTAMP_LONG'])


@app.template_filter()
def timestamp_short(date):
    return date.strftime(app.config['IB2_TIMESTAMP_SHORT'])


@app.template_filter()
def datestamp(date):
    return date.strftime(app.config['IB2_DATESTAMP'])

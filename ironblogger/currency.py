
def format_usd(cents):
    """Format cents like $5.23.

    cents should be an amount of money in USD cents.
    """
    return '$%d.%02d' % (cents / 100, cents % 100)

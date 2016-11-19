from typing import NewType

Cents = NewType('Cents', int)

def format_usd(cents: Cents) -> str:
    """Format cents like $5.23.

    cents should be an amount of money in USD cents.
    """
    return '$%d.%02d' % (cents / 100, cents % 100)

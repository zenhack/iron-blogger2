
from ironblogger.currency import format_usd


assert format_usd(1208) == "$12.08"
assert format_usd(500)  == "$5.00"
assert format_usd(25)   == "$0.25"
assert format_usd(4)    == "$0.04"
assert format_usd(0)    == "$0.00"

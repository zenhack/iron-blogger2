from datetime import datetime, timedelta
from typing import Union


_dt = datetime

class Arrow(object):

    def __sub__(self, other: Arrow) -> timedelta: ...

    def ceil(self, field: str) -> Arrow: ...

    def replace(self,
                hours: int = ...,
                weeks: int = ...) -> Arrow: ...

    def strftime(self, format_string: str) -> str: ...

    def to(self, tzname: str) -> Arrow: ...


    datetime = ... # type: _dt

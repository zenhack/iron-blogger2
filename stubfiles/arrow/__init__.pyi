
from .arrow import Arrow
from typing import Union
from datetime import datetime

_get_arg = Union[str, datetime, Arrow]

def get(t: _get_arg) -> Arrow: ...

def now() -> Arrow: ...

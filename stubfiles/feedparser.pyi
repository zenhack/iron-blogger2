
from typing import List, Dict

USER_AGENT = ... # type: str

class SummaryDetail(object):
    type = ... # type: str

class Entry(Dict[str, str]):
    id = ... # type: str
    summary_detail = ... # type: SummaryDetail

class _Feed(object):
    status = ... # type: int
    entries = ... # type: List[Entry]

def parse(url: str, etag: str = ..., modified: str = ...) -> _Feed: ...

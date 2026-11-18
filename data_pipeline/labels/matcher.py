"""Primary horizon matcher: bisect over monotonic source/session segments."""
from bisect import bisect_left
from dataclasses import dataclass
from decimal import Decimal

@dataclass(frozen=True)
class MarketRow:
    source_id: str
    session_id: str
    record_index: int
    feature_view: str
    event_time_ms: int
    mid_price: Decimal | None
    valid_feature_row: bool

def segments(rows):
    """Yield contiguous same-source/session monotonic segments; never bridge rollback."""
    start = 0
    for i in range(1, len(rows)):
        a, b = rows[i-1], rows[i]
        if (a.source_id, a.session_id) != (b.source_id, b.session_id) or b.event_time_ms < a.event_time_ms:
            yield start, i, b.event_time_ms < a.event_time_ms
            start = i
    if rows:
        yield start, len(rows), False

def first_target(rows, times, index, horizon, end):
    if horizon not in (100, 200, 500, 1000):
        raise ValueError("UNSUPPORTED_HORIZON")
    pos = bisect_left(times, rows[index].event_time_ms + horizon, index + 1, end)
    return pos if pos < end else None

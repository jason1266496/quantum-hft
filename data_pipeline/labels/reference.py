"""Independent linear reference matcher for fixtures and bounded samples."""
from decimal import Decimal, Context, ROUND_HALF_EVEN

_REFERENCE_CONTEXT = Context(prec=50, rounding=ROUND_HALF_EVEN)

def reference_label(rows, index, horizon, end, backward_boundary=False):
    if horizon not in (100, 200, 500, 1000):
        raise ValueError("UNSUPPORTED_HORIZON")
    current = rows[index]
    target = None
    requested = current.event_time_ms + horizon
    for j in range(index + 1, end):
        candidate = rows[j]
        if (candidate.source_id, candidate.session_id) != (current.source_id, current.session_id):
            break
        if candidate.event_time_ms < rows[j-1].event_time_ms:
            break
        if candidate.event_time_ms >= requested:
            target = candidate
            break
    actual = None if target is None else target.event_time_ms - current.event_time_ms
    error = None if actual is None else actual - horizon
    reason = ""
    if not current.valid_feature_row:
        reason = "INVALID_CURRENT_FEATURE_ROW"
    elif current.mid_price is None or current.mid_price <= 0:
        reason = "INVALID_CURRENT_PRICE"
    elif target is None:
        reason = "EVENT_TIME_BACKWARDS" if backward_boundary else "SESSION_TAIL_INSUFFICIENT"
    elif not target.valid_feature_row:
        reason = "INVALID_FUTURE_FEATURE_ROW"
    elif target.mid_price is None or target.mid_price <= 0:
        reason = "INVALID_FUTURE_PRICE"
    value = None
    if not reason:
        value = _REFERENCE_CONTEXT.multiply(
            _REFERENCE_CONTEXT.subtract(
                _REFERENCE_CONTEXT.divide(target.mid_price, current.mid_price), Decimal("1")
            ), Decimal("10000"))
    return {
        "target_event_time_ms": None if target is None else target.event_time_ms,
        "actual_horizon_ms": actual, "match_error_ms": error,
        "future_mid_price": None if target is None else target.mid_price,
        "future_return_bps": value, "valid_label": not bool(reason),
        "invalid_reason": reason,
    }

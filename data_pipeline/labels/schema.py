"""Fixed label schema and decimal serialization."""
from decimal import Decimal, Context, ROUND_HALF_EVEN

HORIZONS_MS = (100, 200, 500, 1000)
LABEL_FIELDS = (
    "source_id", "session_id", "record_index", "feature_view",
    "requested_horizon_ms", "current_event_time_ms", "target_event_time_ms",
    "actual_horizon_ms", "match_error_ms", "current_mid_price",
    "future_mid_price", "future_return_bps", "valid_label", "invalid_reason",
)
INVALID_REASONS = frozenset((
    "SESSION_TAIL_INSUFFICIENT", "INVALID_CURRENT_PRICE", "INVALID_FUTURE_PRICE",
    "INVALID_CURRENT_FEATURE_ROW", "INVALID_FUTURE_FEATURE_ROW",
    "EVENT_TIME_BACKWARDS",
))
CONTEXT = Context(prec=50, rounding=ROUND_HALF_EVEN)
DECIMAL_FIELDS = frozenset(("current_mid_price", "future_mid_price", "future_return_bps"))
INTEGER_FIELDS = frozenset(("record_index", "requested_horizon_ms", "current_event_time_ms",
                            "target_event_time_ms", "actual_horizon_ms", "match_error_ms"))
STRING_FIELDS = frozenset(("source_id", "session_id", "feature_view", "invalid_reason"))

def decimal_text(value):
    if value is None:
        return ""
    if type(value) is not Decimal or not value.is_finite():
        raise ValueError("FINITE_DECIMAL_REQUIRED")
    if value == 0:
        return "0"
    return format(value, "f").rstrip("0").rstrip(".") if "." in format(value, "f") else format(value, "f")

def decimal_input(value):
    try:
        result = Decimal(value)
    except Exception as exc:
        raise ValueError("INVALID_PRICE") from exc
    return result if result.is_finite() else None

def return_bps(current, future):
    if type(current) is not Decimal or type(future) is not Decimal:
        raise ValueError("DECIMAL_REQUIRED")
    return CONTEXT.multiply(CONTEXT.subtract(CONTEXT.divide(future, current), Decimal(1)), Decimal(10000))

def schema_document():
    return {
        "schema_version": "1.0", "label_kind": "continuous_future_return_bps",
        "field_order": list(LABEL_FIELDS), "horizons_ms": list(HORIZONS_MS),
        "time_field": "event_time_ms", "matching": "first event >= current event time + horizon within source/session/monotonic segment",
        "max_match_error_ms": None, "gap_threshold_ms": None,
        "decimal_policy": {"precision": 50, "rounding": "ROUND_HALF_EVEN", "float_used": False},
        "local_timestamp_us_in_output": False, "class_labels": False,
        "invalid_reasons": sorted(INVALID_REASONS),
    }

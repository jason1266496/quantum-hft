"""Strict Phase 2C feature input and Phase 2D label validation."""
import csv
import json
from pathlib import Path
from decimal import Decimal
from .schema import LABEL_FIELDS, HORIZONS_MS, decimal_input
from .matcher import MarketRow

PHASE2C_RUN = "20261019T001249Z"
VIEWS = ("aggregate_core_v1", "depth_top5_v1")
CSV_SOURCES = (
    "obi_market_data_20260827_session1",
    "obi_market_data_20260827_session2",
    "obi_market_data_20260827_session3",
    "obi_market_data_test_20260827",
    "obi_market_data",
)
REPLAY_SOURCES = ("replay_events_1000", "replay_events_50000")
SOURCES = CSV_SOURCES + REPLAY_SOURCES

def feature_path(root, source_id, view):
    if source_id not in SOURCES or view not in VIEWS:
        raise ValueError("UNAPPROVED_SOURCE_OR_VIEW")
    if source_id in CSV_SOURCES and view != "aggregate_core_v1":
        raise ValueError("CSV_DEPTH_NOT_AVAILABLE")
    path = Path(root) / "artifacts/phase2c" / PHASE2C_RUN / "sources" / source_id / (view + ".csv")
    if path.is_symlink() or not path.is_file():
        raise ValueError("FEATURE_INPUT_NOT_REGULAR")
    return path

def read_feature_rows(root, source_id, view):
    path = feature_path(root, source_id, view)
    schema_path = Path(root) / "artifacts/phase2c" / PHASE2C_RUN / "schemas" / (view + ".schema.json")
    expected = json.loads(schema_path.read_text(encoding="utf-8"))["field_order"]
    rows = []
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != expected or "local_timestamp_us" in reader.fieldnames:
            raise ValueError("FEATURE_SCHEMA_MISMATCH")
        identity = None
        last_index = 0
        for raw in reader:
            if None in raw or set(raw) != set(expected):
                raise ValueError("FEATURE_ROW_FIELD_MISMATCH")
            if raw["source_id"] != source_id or raw["feature_view"] != view:
                raise ValueError("CROSS_SOURCE_OR_VIEW_INPUT")
            pair = (raw["source_id"], raw["session_id"])
            if not pair[1]:
                raise ValueError("EMPTY_SESSION_ID")
            if identity is None:
                identity = pair
            elif pair != identity:
                raise ValueError("CROSS_SESSION_INPUT")
            try:
                record_index = int(raw["record_index"])
                event_time = int(raw["event_time_ms"])
            except ValueError as exc:
                raise ValueError("INVALID_EVENT_METADATA") from exc
            if record_index <= last_index or event_time < 0:
                raise ValueError("RECORD_INDEX_OR_EVENT_TIME_INVALID")
            last_index = record_index
            if raw["valid_feature_row"] not in ("true", "false"):
                raise ValueError("INVALID_FEATURE_FLAG")
            try:
                mid = decimal_input(raw["mid_price"])
            except ValueError:
                mid = None
            rows.append(MarketRow(source_id, pair[1], record_index, view, event_time,
                                  mid, raw["valid_feature_row"] == "true"))
    return rows

def validate_label(row):
    if type(row) is not dict or tuple(row) != LABEL_FIELDS:
        raise ValueError("LABEL_SCHEMA_MISMATCH")
    if row["requested_horizon_ms"] not in HORIZONS_MS:
        raise ValueError("UNSUPPORTED_HORIZON")
    if row["valid_label"] not in (True, False) or type(row["valid_label"]) is not bool:
        raise ValueError("INVALID_VALIDITY")
    if row["valid_label"] and row["invalid_reason"]:
        raise ValueError("VALID_LABEL_WITH_REASON")
    if not row["valid_label"] and not row["invalid_reason"]:
        raise ValueError("INVALID_LABEL_WITHOUT_REASON")
    if row["target_event_time_ms"] is None:
        if row["actual_horizon_ms"] is not None or row["match_error_ms"] is not None:
            raise ValueError("UNMATCHED_WITH_HORIZON")
    else:
        if row["actual_horizon_ms"] != row["target_event_time_ms"] - row["current_event_time_ms"]:
            raise ValueError("INCORRECT_ACTUAL_HORIZON")
        if row["match_error_ms"] != row["actual_horizon_ms"] - row["requested_horizon_ms"]:
            raise ValueError("INCORRECT_MATCH_ERROR")
        if row["match_error_ms"] < 0:
            raise ValueError("NEGATIVE_MATCH_ERROR")
    if row["valid_label"]:
        for name in ("current_mid_price", "future_mid_price", "future_return_bps"):
            if type(row[name]) is not Decimal or not row[name].is_finite():
                raise ValueError("VALID_LABEL_DECIMAL_REQUIRED")
        if row["current_mid_price"] <= 0 or row["future_mid_price"] <= 0:
            raise ValueError("VALID_LABEL_POSITIVE_PRICE_REQUIRED")
    elif row["future_return_bps"] is not None:
        raise ValueError("INVALID_LABEL_RETURN_MUST_BE_NULL")
    return True

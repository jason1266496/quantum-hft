"""Explicit feature contracts and stable schema hashes (no market access)."""

import hashlib
import json

SCHEMA_VERSION = "1.0"
VIEWS = ("aggregate_core_v1", "depth_top5_v1")
META_FIELDS = ("schema_version", "feature_view", "source_id", "session_id",
               "record_index", "event_time_ms", "first_update_id", "final_update_id",
               "local_update_id")
QUALITY_FIELDS = ("valid_feature_row", "invalid_reason")
AGGREGATE_VALUES = ("best_bid", "best_ask", "mid_price", "spread", "spread_bps",
                    "bid_volume_5", "ask_volume_5", "obi_5")
DEPTH_VALUES = tuple(
    f"{prefix}_{i}" for prefix in (
        "bid_price", "bid_quantity", "ask_price", "ask_quantity",
        "cumulative_bid_quantity", "cumulative_ask_quantity",
        "bid_distance_bps", "ask_distance_bps", "level_imbalance"
    ) for i in range(1, 6)
) + ("obi_1", "obi_3", "obi_5", "mid_price", "spread", "spread_bps",
     "microprice", "microprice_deviation_bps")


def fields(view):
    """Return the authoritative order; insertion order never defines a schema."""
    if view not in VIEWS:
        raise ValueError("UNKNOWN_FEATURE_VIEW")
    return META_FIELDS + (AGGREGATE_VALUES if view == VIEWS[0] else DEPTH_VALUES) + QUALITY_FIELDS


def _formula(name):
    explicit = {
        "best_bid": "highest bid price", "best_ask": "lowest ask price",
        "mid_price": "(best_bid + best_ask) / 2",
        "spread": "best_ask - best_bid",
        "spread_bps": "spread / mid_price * 10000",
        "bid_volume_5": "sum(bid_quantity_i, i=1..5)",
        "ask_volume_5": "sum(ask_quantity_i, i=1..5)",
        "microprice": "(best_ask * bid_quantity_1 + best_bid * ask_quantity_1) / (bid_quantity_1 + ask_quantity_1)",
        "microprice_deviation_bps": "(microprice - mid_price) / mid_price * 10000",
        "valid_feature_row": "no invalidating quality condition",
        "invalid_reason": "semicolon-joined sorted unique condition codes; ZERO_LEVEL_DENOMINATOR alone is a warning",
    }
    if name in explicit:
        return explicit[name]
    if name.startswith("obi_"):
        k = name.rsplit("_", 1)[1]
        return f"(bid_volume_{k} - ask_volume_{k}) / (bid_volume_{k} + ask_volume_{k})"
    for side in ("bid", "ask"):
        if name.startswith("cumulative_" + side + "_quantity_"):
            return f"sum({side}_quantity_j, j=1..{name.rsplit('_', 1)[1]})"
        if name.startswith(side + "_distance_bps_"):
            i = name.rsplit("_", 1)[1]
            numerator = f"mid_price - bid_price_{i}" if side == "bid" else f"ask_price_{i} - mid_price"
            return f"({numerator}) / mid_price * 10000"
    if name.startswith("level_imbalance_"):
        i = name.rsplit("_", 1)[1]
        return f"(bid_quantity_{i} - ask_quantity_{i}) / (bid_quantity_{i} + ask_quantity_{i})"
    if name in META_FIELDS:
        return "identity or provenance metadata; no predictive calculation"
    return "current completed-event book level, ordered bids descending / asks ascending"


def _metadata(name, view):
    numeric = name not in META_FIELDS + QUALITY_FIELDS
    integer = name in ("record_index", "event_time_ms", "first_update_id", "final_update_id", "local_update_id")
    unit = "NOT_APPLICABLE"
    if numeric:
        unit = ("bps" if "bps" in name else "ratio" if name.startswith(("obi_", "level_imbalance_"))
                else "base_asset_quantity" if "quantity" in name or "volume" in name
                else "quote_asset_per_base_asset")
    if name == "event_time_ms":
        unit = "milliseconds_since_Unix_epoch"
    allowed = "finite Decimal; invalid inputs become null with a reason"
    if name.startswith(("obi_", "level_imbalance_")):
        allowed = "[-1, 1]"
    elif name == "microprice":
        allowed = "[best_bid, best_ask]"
    elif numeric and ("quantity" in name or "volume" in name or "distance" in name):
        allowed = ">= 0"
    elif numeric and name != "microprice_deviation_bps":
        allowed = "> 0"
    elif integer:
        allowed = ">= 1" if name == "record_index" else ">= 0"
    elif name == "valid_feature_row":
        allowed = "true or false"
    elif not numeric:
        allowed = "nonempty identity/version string; invalid_reason may be empty"
    notes = []
    if name in META_FIELDS:
        notes.append("Metadata only; excluded from predictive features, including raw event_time_ms.")
    if name == "session_id":
        notes.append("Registry research alias, not proof of capture identity; never merge sources or sessions.")
    if name == "local_update_id":
        notes.append("Replay: current rebuilder ID. CSV: direct alias of provided update_id only; historical producer UNKNOWN; not independent reconstruction evidence.")
    if name in ("first_update_id", "final_update_id"):
        notes.append("CSV is null; do not infer an update range. Replay contains the actual event IDs.")
    if name.startswith("level_imbalance_"):
        notes.append("Zero denominator produces null and ZERO_LEVEL_DENOMINATOR warning.")
    if name.startswith("obi_"):
        notes.append("Zero denominator invalidates the row; never substitute zero.")
    if numeric:
        notes.append("Null preserves invalid or unavailable data; no future fill, imputation or silent row deletion.")
    return {
        "name": name,
        "data_type": "canonical_decimal_string" if numeric else "integer" if integer else "boolean" if name == "valid_feature_row" else "string",
        "nullable": numeric or integer or name in ("source_id", "session_id"),
        "unit": unit, "formula": _formula(name),
        "source": "current CSV row or completed Replay event" if view == VIEWS[0] else "current completed-event reconstructed book only",
        "allowed_range": allowed,
        "availability": "CSV_AND_REPLAY" if view == VIEWS[0] else "REPLAY_ONLY; CSV_NOT_AVAILABLE",
        "leakage_risk": "METADATA_NOT_MODEL_FEATURE" if name in META_FIELDS else "CURRENT_EVENT_ONLY; no future input",
        "notes": notes,
    }


def feature_schema(view):
    """Return fresh JSON-safe metadata; formulas use a declared 50-digit context."""
    return {
        "schema_version": SCHEMA_VERSION, "feature_view": view,
        "field_order": list(fields(view)),
        "fields": [_metadata(name, view) for name in fields(view)],
        "numeric_policy": {
            "input": "finite Decimal only; no float conversion",
            "precision": 50, "rounding": "ROUND_HALF_EVEN", "Emin": -999999, "Emax": 999999,
            "context": "fresh explicit Decimal Context per calculation, independent of caller context",
            "output": "canonical fixed-point strings; normalize negative zero to 0; remove insignificant fractional zeros",
            "source_rounding": "UNKNOWN; computational precision does not infer historical producer rounding",
            "missing": "null in memory/JSON; empty CSV cell",
        },
        "excluded_fields": {
            "local_timestamp_us": "PROHIBITED",
            "future_return": "NOT_PRESENT", "target_label": "NOT_PRESENT",
            "per_level_depth_on_csv": "NOT_AVAILABLE",
            "depth_slope": "NOT_PRESENT", "rolling_volatility": "NOT_PRESENT",
            "rolling_return": "NOT_PRESENT", "order_arrival_rate": "NOT_PRESENT",
        },
        "time_policy": "event_time_ms ordering metadata only; source order retained; no shuffle, future lookahead, centered windows or cross-session merge",
        "quality_policy": "invalid rows retained; missing top-five depth invalid; no fabricated update IDs",
    }


def schema_hash(view):
    serialized = json.dumps(feature_schema(view), sort_keys=True, ensure_ascii=True,
                            separators=(",", ":"), allow_nan=False).encode("utf-8")
    return hashlib.sha256(serialized).hexdigest()

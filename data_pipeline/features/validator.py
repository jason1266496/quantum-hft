"""Deterministic per-source feature quality checks; no rows are discarded."""

from __future__ import annotations

from collections import Counter
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext

from data_pipeline.orderbook.canonical import canonical_decimal
from .schema import fields

CALCULATION_CONTEXT = Context(prec=50, rounding=ROUND_HALF_EVEN)
SOURCE_ABSOLUTE_TOLERANCE = Decimal("0.00000001")
SOURCE_FIELDS = ("mid_price", "spread", "obi_5")
TEXT_FIELDS = {"schema_version", "feature_view", "source_id", "session_id", "invalid_reason"}
ID_FIELDS = {"record_index", "event_time_ms", "first_update_id", "final_update_id", "local_update_id"}
COUNT_FIELDS = (
    "input_record_count", "output_record_count", "valid_feature_rows", "invalid_feature_rows",
    "missing_values", "non_finite_values", "crossed_book_rows", "insufficient_depth_rows",
    "zero_denominator_rows", "obi_out_of_range", "level_imbalance_out_of_range",
    "microprice_out_of_spread", "event_time_backwards", "duplicate_event_time",
    "update_id_backwards", "source_value_mismatch_count", "source_value_mismatch_rows",
)
HISTOGRAM_KEYS = ("zero", "0_to_1e-12_inclusive", "1e-12_to_1e-10_inclusive",
                  "1e-10_to_1e-8_inclusive", "greater_than_1e-8")


def _finite(value):
    return type(value) is Decimal and value.is_finite()


def _safe(value):
    if isinstance(value, Decimal):
        return canonical_decimal(value) if value.is_finite() else str(value)
    if isinstance(value, dict):
        return {key: _safe(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_safe(item) for item in value]
    return value


def _distribution():
    return {
        "count": 0, "nonzero_count": 0, "mismatch_count": 0,
        "minimum_absolute_difference": None, "maximum_absolute_difference": None,
        "sum_absolute_difference": Decimal(0), "sum_signed_difference": Decimal(0),
        "histogram": dict.fromkeys(HISTOGRAM_KEYS, 0),
        "nonzero_samples": [],
    }


class FeatureValidator:
    """Observe only one view/source/session. Summary never includes clocks."""

    def __init__(self, source_id, session_id, view, source_kind):
        if any(type(value) is not str or not value for value in (source_id, session_id)):
            raise ValueError("INVALID_SOURCE_IDENTITY")
        if source_kind not in ("csv", "replay", "jsonl"):
            raise ValueError("INVALID_SOURCE_KIND")
        if source_kind == "csv" and view != "aggregate_core_v1":
            raise ValueError("CSV_DEPTH_VIEW_PROHIBITED")
        self.source_id = source_id
        self.session_id = session_id
        self.view = view
        self.source_kind = source_kind
        self._fields = tuple(fields(view))
        self._counts = dict.fromkeys(COUNT_FIELDS, 0)
        self._missing = Counter()
        self._non_finite = Counter()
        self._invalid_reasons = Counter()
        self._warnings = Counter()
        self._seen_event_times = set()
        self._last_event_time = None
        self._last_update_id = None
        self._differences = {name: _distribution() for name in SOURCE_FIELDS}
        self.source_differences = []

    def _compare_source(self, row, source_record, reasons):
        self.source_differences = []
        if self.source_kind != "csv" or source_record is None:
            return
        row_mismatch = False
        for name in SOURCE_FIELDS:
            original, computed = source_record.get(name), row.get(name)
            if not _finite(original) or not _finite(computed):
                self._warnings["SOURCE_VALUE_COMPARISON_NOT_AVAILABLE:" + name] += 1
                continue
            with localcontext(CALCULATION_CONTEXT):
                signed = original - computed
                difference = abs(signed)
                dist = self._differences[name]
                dist["count"] += 1
                dist["nonzero_count"] += int(difference != 0)
                dist["sum_absolute_difference"] += difference
                dist["sum_signed_difference"] += signed
            if dist["minimum_absolute_difference"] is None or difference < dist["minimum_absolute_difference"]:
                dist["minimum_absolute_difference"] = difference
            if dist["maximum_absolute_difference"] is None or difference > dist["maximum_absolute_difference"]:
                dist["maximum_absolute_difference"] = difference
            if difference == 0:
                bucket = HISTOGRAM_KEYS[0]
            elif difference <= Decimal("1e-12"):
                bucket = HISTOGRAM_KEYS[1]
            elif difference <= Decimal("1e-10"):
                bucket = HISTOGRAM_KEYS[2]
            elif difference <= SOURCE_ABSOLUTE_TOLERANCE:
                bucket = HISTOGRAM_KEYS[3]
            else:
                bucket = HISTOGRAM_KEYS[4]
            dist["histogram"][bucket] += 1
            comparison = {
                "record_index": row.get("record_index"), "field": name,
                "original": original, "computed": computed, "difference": difference,
                "signed_difference": signed, "tolerance": SOURCE_ABSOLUTE_TOLERANCE,
                "within_tolerance": difference <= SOURCE_ABSOLUTE_TOLERANCE,
            }
            self.source_differences.append(_safe(comparison))
            if difference != 0 and len(dist["nonzero_samples"]) < 20:
                dist["nonzero_samples"].append(_safe(comparison))
            if difference > SOURCE_ABSOLUTE_TOLERANCE:
                dist["mismatch_count"] += 1
                self._counts["source_value_mismatch_count"] += 1
                row_mismatch = True
        if row_mismatch:
            self._counts["source_value_mismatch_rows"] += 1
            reasons.add("SOURCE_VALUE_MISMATCH")

    def observe(self, row, source_record=None):
        if not isinstance(row, dict) or set(row) != set(self._fields):
            raise ValueError("FEATURE_FIELDS_MUST_EXACTLY_MATCH_SCHEMA")
        if (row.get("source_id"), row.get("session_id"), row.get("feature_view")) != (
            self.source_id, self.session_id, self.view
        ):
            raise ValueError("SOURCE_SESSION_OR_VIEW_MISMATCH")
        row = dict(row)
        reasons = {value for value in str(row.get("invalid_reason") or "").split(";") if value}
        warning_reasons = reasons & {"ZERO_LEVEL_DENOMINATOR"}
        reasons.difference_update(warning_reasons)
        for warning in warning_reasons:
            self._warnings[warning] += 1
        if row.get("valid_feature_row") is not True and not reasons:
            reasons.add("SOURCE_MARKED_INVALID")
        self._counts["input_record_count"] += 1
        self._counts["output_record_count"] += 1
        optional_ids = {"first_update_id", "final_update_id", "local_update_id"} if self.source_kind == "csv" else set()
        numeric = [name for name in self._fields if name not in TEXT_FIELDS | ID_FIELDS | {"valid_feature_row"}]
        for name in numeric:
            value = row[name]
            if value is None:
                self._counts["missing_values"] += 1
                self._missing[name] += 1
            elif type(value) is not Decimal:
                reasons.add("INVALID_NUMERIC_TYPE")
                row[name] = None
                self._counts["missing_values"] += 1
                self._missing[name] += 1
            elif not value.is_finite():
                self._counts["non_finite_values"] += 1
                self._non_finite[name] += 1
                reasons.add("NON_FINITE_VALUE")
                row[name] = None
        for name in ID_FIELDS:
            value = row.get(name)
            if value is None:
                self._counts["missing_values"] += 1
                self._missing[name] += 1
                if name not in optional_ids:
                    reasons.add("MISSING_EVENT_METADATA")
            elif type(value) is not int or value < 0 or (name == "record_index" and value == 0):
                reasons.add("INVALID_EVENT_METADATA")
                row[name] = None
        for name in ("best_bid", "best_ask", "mid_price"):
            if name in row and _finite(row[name]) and row[name] <= 0:
                reasons.add("INVALID_PRICE")
        for name in numeric:
            value = row[name]
            if not _finite(value):
                continue
            if ("_price_" in name or name == "microprice") and value <= 0:
                reasons.add("INVALID_PRICE")
            if ("quantity" in name or name in ("bid_volume_5", "ask_volume_5")) and value < 0:
                reasons.add("INVALID_QUANTITY")
        if self.view == "aggregate_core_v1":
            bid, ask = row.get("best_bid"), row.get("best_ask")
            essential = ("best_bid", "best_ask", "mid_price", "spread", "spread_bps",
                         "bid_volume_5", "ask_volume_5", "obi_5")
            if any(row.get(name) is None for name in essential):
                reasons.add("MISSING_FEATURE_VALUE")
            bv, av = row.get("bid_volume_5"), row.get("ask_volume_5")
            if _finite(bv) and _finite(av) and bv + av == 0:
                reasons.add("ZERO_DEPTH_DENOMINATOR")
        else:
            bid, ask = row.get("bid_price_1"), row.get("ask_price_1")
            level_fields = tuple(f"{side}_{kind}_{i}" for side in ("bid", "ask")
                                 for kind in ("price", "quantity") for i in range(1, 6))
            if any(row.get(name) is None for name in level_fields):
                reasons.add("INSUFFICIENT_TOP5_DEPTH")
            if bid is None or ask is None:
                reasons.add("EMPTY_BOOK_SIDE")
            with localcontext(CALCULATION_CONTEXT):
                for i in range(1, 6):
                    bq, aq = row.get(f"bid_quantity_{i}"), row.get(f"ask_quantity_{i}")
                    if _finite(bq) and _finite(aq) and bq + aq == 0:
                        warning_reasons.add("ZERO_LEVEL_DENOMINATOR")
                        self._warnings[f"ZERO_LEVEL_DENOMINATOR:{i}"] += 1
                        if row.get(f"level_imbalance_{i}") is not None:
                            reasons.add("UNDEFINED_LEVEL_IMBALANCE_NOT_EMPTY")
                for k in (1, 3, 5):
                    quantities = [row.get(f"{side}_quantity_{i}") for side in ("bid", "ask")
                                  for i in range(1, k + 1)]
                    if all(_finite(value) for value in quantities) and sum(quantities, Decimal(0)) == 0:
                        reasons.add("ZERO_DEPTH_DENOMINATOR")
            optional_zero_level = {
                f"level_imbalance_{i}" for i in range(1, 6)
                if _finite(row.get(f"bid_quantity_{i}")) and _finite(row.get(f"ask_quantity_{i}"))
                and row[f"bid_quantity_{i}"] + row[f"ask_quantity_{i}"] == 0
            }
            if any(row.get(name) is None for name in numeric if name not in optional_zero_level):
                reasons.add("MISSING_FEATURE_VALUE")
        crossed = _finite(bid) and _finite(ask) and bid >= ask
        if crossed:
            reasons.add("CROSSED_BOOK")
        if _finite(row.get("spread")) and row["spread"] <= 0:
            reasons.add("NONPOSITIVE_SPREAD")
        for name in ("obi_1", "obi_3", "obi_5"):
            if _finite(row.get(name)) and not Decimal(-1) <= row[name] <= Decimal(1):
                self._counts["obi_out_of_range"] += 1
                reasons.add("OBI_OUT_OF_RANGE")
        for i in range(1, 6):
            value = row.get(f"level_imbalance_{i}")
            if _finite(value) and not Decimal(-1) <= value <= Decimal(1):
                self._counts["level_imbalance_out_of_range"] += 1
                reasons.add("LEVEL_IMBALANCE_OUT_OF_RANGE")
        mp = row.get("microprice")
        if _finite(mp) and _finite(bid) and _finite(ask) and not bid <= mp <= ask:
            self._counts["microprice_out_of_spread"] += 1
            reasons.add("MICROPRICE_OUT_OF_SPREAD")
        time = row.get("event_time_ms")
        if type(time) is int:
            if self._last_event_time is not None and time < self._last_event_time:
                self._counts["event_time_backwards"] += 1
                reasons.add("EVENT_TIME_BACKWARDS")
            if time in self._seen_event_times:
                self._counts["duplicate_event_time"] += 1
                reasons.add("DUPLICATE_EVENT_TIME")
            self._seen_event_times.add(time)
            self._last_event_time = time
        update_id = row.get("local_update_id")
        if type(update_id) is int:
            if self._last_update_id is not None and update_id < self._last_update_id:
                self._counts["update_id_backwards"] += 1
                reasons.add("UPDATE_ID_BACKWARDS")
            self._last_update_id = update_id
        self._compare_source(row, source_record, reasons)
        self._counts["crossed_book_rows"] += int(crossed or "CROSSED_BOOK" in reasons)
        self._counts["insufficient_depth_rows"] += int("INSUFFICIENT_TOP5_DEPTH" in reasons)
        self._counts["zero_denominator_rows"] += int("ZERO_DEPTH_DENOMINATOR" in reasons)
        row["invalid_reason"] = ";".join(sorted(reasons | warning_reasons))
        row["valid_feature_row"] = not reasons
        self._counts["valid_feature_rows"] += int(not reasons)
        self._counts["invalid_feature_rows"] += int(bool(reasons))
        self._invalid_reasons.update(reasons)
        return row

    def summary(self):
        maximums = {field: data["maximum_absolute_difference"]
                    for field, data in self._differences.items()}
        return _safe({
            "source_id": self.source_id, "session_id": self.session_id,
            "feature_view": self.view, "source_kind": self.source_kind, **self._counts,
            "missing_values_by_field": dict(sorted(self._missing.items())),
            "non_finite_values_by_field": dict(sorted(self._non_finite.items())),
            "invalid_reasons": dict(sorted(self._invalid_reasons.items())),
            "quality_warnings": dict(sorted(self._warnings.items())),
            "source_value_differences": self._differences,
            "maximum_source_value_difference": maximums,
            "source_value_comparison_absolute_tolerance": SOURCE_ABSOLUTE_TOLERANCE,
            "source_value_comparison_relative_tolerance": "NOT_PRESENT",
            "source_value_mismatch_unit": "field_comparisons_strictly_greater_than_absolute_tolerance",
            "source_value_comparison_difference_direction": "original_minus_recomputed",
            "decimal_context": {"precision": 50, "rounding": "ROUND_HALF_EVEN"},
            "csv_update_id_semantics": (
                "CSV update_id direct alias; exact historical producer UNKNOWN; not event U/u"
                if self.source_kind == "csv" else "NOT_APPLICABLE"
            ),
            "local_timestamp_us_in_feature_view": False,
            "future_labels_present": False,
            "record_count_scope": "Each observe call is one output row; Replay skips are counted by caller.",
        })


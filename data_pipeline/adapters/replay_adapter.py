"""Bounded, read-only parsing of normalized Replay JSONL; no book updates."""

from __future__ import annotations

import json
from decimal import Decimal, InvalidOperation
from itertools import islice

from .base import BaseAdapter, DataFormatError, parse_decimal


MAX_LINE_BYTES = 4_194_304
REQUIRED_FIELDS = ("eventTime", "firstUpdateId", "finalUpdateId", "bids", "asks")
UPDATE_FIELDS = ("price", "quantity")
SCHEMA_VARIANT = "capture_object_price_quantity_v1"
MAX_SAFE_SUMMARY_CHARACTERS = 192


def _reject_constant(value):
    raise ValueError("non-finite JSON constant: " + value)


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def _safe_summary(value):
    """Bound and escape diagnostic input; never serialize a full event or side."""
    def bounded(item, depth=0):
        if isinstance(item, bytes):
            return {"type": "bytes", "prefix_hex": item[:24].hex(), "length": len(item)}
        if isinstance(item, str):
            return item[:64] + ("..." if len(item) > 64 else "")
        if isinstance(item, Decimal):
            text = str(item)
            return {"type": "number", "value": text[:64] + ("..." if len(text) > 64 else "")}
        if type(item) is int:
            return item if item.bit_length() <= 425 else {"type": "integer", "bits": item.bit_length()}
        if isinstance(item, (list, dict)):
            result = {"type": "array" if isinstance(item, list) else "object", "length": len(item)}
            if depth < 2:
                if isinstance(item, list):
                    result["prefix"] = [bounded(child, depth + 1) for child in item[:2]]
                else:
                    result["prefix"] = {str(key)[:32]: bounded(child, depth + 1)
                                        for key, child in islice(item.items(), 3)}
            return result
        return item if item is None or isinstance(item, bool) else {"type": type(item).__name__}

    text = json.dumps(bounded(value), ensure_ascii=True, allow_nan=False)
    if len(text) > MAX_SAFE_SUMMARY_CHARACTERS:
        text = text[:MAX_SAFE_SUMMARY_CHARACTERS - 3] + "..."
    return text


class ReplayAdapter(BaseAdapter):
    """Validate each normalized event independently, preserving registry isolation."""

    def __init__(self, registry, source_id):
        super().__init__(registry, source_id)
        if self.source.file_type != "replay":
            raise ValueError("ReplayAdapter requires a registered replay source")
        self._inspection_summary = None

    def _error(self, index, message, *, side="NOT_AVAILABLE",
               update_index="NOT_AVAILABLE", raw=None):
        summary = _safe_summary(raw)
        context = (f"source_id={self.source.source_id}; record_index={index}; "
                   f"side={side}; update_index={update_index}; raw_summary={summary}")
        error = DataFormatError(self.source.absolute_path, index,
                                f"{message}; {context}", physical_line=index)
        error.source_id = self.source.source_id
        error.side = side
        error.update_index = update_index
        error.safe_summary = summary
        return error

    def _levels(self, value, index, field):
        if not isinstance(value, list):
            raise self._error(index, field + " must be an array", side=field, raw=value)
        levels = []
        for level_index, level in enumerate(value):
            if not isinstance(level, dict) or set(level) != set(UPDATE_FIELDS):
                raise self._error(
                    index, "update must be an object with exactly price and quantity fields",
                    side=field, update_index=level_index, raw=level,
                )
            parsed = []
            for name in UPDATE_FIELDS:
                item = level[name]
                # Capture emits JSON numbers. Do not silently add string/pair variants.
                if type(item) not in (int, Decimal):
                    raise self._error(
                        index, name + " must be a JSON number",
                        side=field, update_index=level_index, raw=item,
                    )
                try:
                    parsed.append(parse_decimal(
                        item, file=self.source.absolute_path, record_index=index,
                        field=field + "[" + str(level_index) + "]." + name,
                        physical_line=index, minimum=0,
                    ))
                except DataFormatError as exc:
                    raise self._error(
                        index, name + " must be a finite nonnegative decimal within numeric bounds",
                        side=field, update_index=level_index, raw=item,
                    ) from exc
            if parsed[0] <= 0:
                raise self._error(index, "price must be positive", side=field,
                                  update_index=level_index, raw=level["price"])
            levels.append(tuple(parsed))
        return tuple(levels)

    def _iter_records(self):
        """Yield lossless Decimal price/quantity pairs; never apply book updates.

        Decimal is constructed directly from each JSON numeric token, without a
        binary float conversion. Numeric value and decimal precision survive;
        whitespace and the original exponent spelling are not retained.
        """
        self.validate_source()
        with self._open_binary() as handle:
            index = 0
            while True:
                line = handle.readline(MAX_LINE_BYTES + 1)
                if not line:
                    break
                index += 1
                if len(line) > MAX_LINE_BYTES:
                    raise self._error(index, "JSONL line exceeds safety limit", raw=line)
                try:
                    line = line.decode("utf-8", errors="strict")
                except UnicodeError as exc:
                    raise self._error(index, "invalid UTF-8", raw=line) from exc
                if not line.strip():
                    raise self._error(index, "empty JSONL record", raw=line)
                try:
                    event = json.loads(
                        line, parse_float=Decimal, parse_constant=_reject_constant,
                        object_pairs_hook=_unique_object,
                    )
                except (ValueError, RecursionError, InvalidOperation) as exc:
                    raise self._error(index, "JSON parse error: " + str(exc), raw=line) from exc
                if not isinstance(event, dict):
                    raise self._error(index, "JSONL event must be an object", raw=event)
                missing = [field for field in REQUIRED_FIELDS if field not in event]
                if missing:
                    raise self._error(index, "missing required fields: " + repr(missing), raw=event)
                if set(event) != set(REQUIRED_FIELDS):
                    raise self._error(index, "unexpected top-level fields", raw=event)
                for field in REQUIRED_FIELDS[:3]:
                    if type(event[field]) is not int or event[field] < 0:
                        raise self._error(index, field + " must be a nonnegative JSON integer", raw=event[field])
                if event["firstUpdateId"] > event["finalUpdateId"]:
                    raise self._error(index, "firstUpdateId exceeds finalUpdateId", raw=event["firstUpdateId"])
                bids = self._levels(event["bids"], index, "bids")
                asks = self._levels(event["asks"], index, "asks")
                yield {
                    "record_index": index, "physical_line": index,
                    "source_id": self.source.source_id, "session_id": self.source.session_id,
                    "schema_variant": SCHEMA_VARIANT,
                    "eventTime": event["eventTime"],
                    "firstUpdateId": event["firstUpdateId"],
                    "finalUpdateId": event["finalUpdateId"],
                    "bid_update_count": len(bids), "ask_update_count": len(asks),
                    "bids": bids, "asks": asks,
                }

    def stream_records(self, limit=None):
        """Stream one source, optionally stopping after a bounded number of records."""
        if limit is not None and (type(limit) is not int or limit <= 0):
            raise ValueError("limit must be a positive integer or None")
        records = self._iter_records()
        try:
            yield from records if limit is None else islice(records, limit)
        finally:
            records.close()

    def inspect_schema(self, sample_records=100):
        """Bound schema checking to the requested records; do not persist source events."""
        if sample_records is not None and (
            type(sample_records) is not int or sample_records <= 0
        ):
            raise ValueError("sample_records must be a positive integer or None")
        summary = {
            "source_id": self.source.source_id, "session_id": self.source.session_id,
            "session_id_semantics": "research_registry_alias_not_capture_identity",
            "adapter": type(self).__name__, "file_type": "replay", "status": "PASS",
            "checked_records": 0, "parse_errors": 0,
            "full_scan": sample_records is None, "sample_limit": sample_records,
            "schema_scope": "all_records" if sample_records is None else "at_most_sample_limit_records",
            "required_fields": list(REQUIRED_FIELDS),
            "schema_variant": SCHEMA_VARIANT,
            "update_schema": {"container": "array", "item": "object",
                              "exact_fields": list(UPDATE_FIELDS), "value_type": "JSON_number"},
            "error_update_index_base": 0,
            "event_time_start_observed": None, "event_time_end_observed": None,
            "bid_updates_checked": 0, "ask_updates_checked": 0,
            "numeric_representation": "JSON_int_ids_and_finite_Decimal_price_quantity",
            "timestamp_policy": {
                "order_field": "eventTime",
                "event_time_role": "exchange_event_metadata",
                "local_receive_time": "NOT_AVAILABLE",
                "cross_session_merge": False,
            },
            "snapshot_applied": False, "order_book_updated": False,
            "obi_computed": False, "derived_features": False, "future_labels": False,
        }
        records = self.stream_records()
        self._inspection_summary = summary
        try:
            selected = records if sample_records is None else islice(records, sample_records)
            for record in selected:
                if summary["checked_records"] == 0:
                    summary["event_time_start_observed"] = record["eventTime"]
                summary["event_time_end_observed"] = record["eventTime"]
                summary["checked_records"] += 1
                summary["bid_updates_checked"] += record["bid_update_count"]
                summary["ask_updates_checked"] += record["ask_update_count"]
            if not summary["checked_records"]:
                raise self._error(1, "Replay contains no events")
        except DataFormatError:
            summary["status"] = "FAIL"
            summary["parse_errors"] += 1
            raise
        finally:
            records.close()
        return summary

    def summarize(self):
        """Return cached inspection metadata only."""
        self._ensure_open()
        if self._inspection_summary is None:
            return {
                "source_id": self.source.source_id, "session_id": self.source.session_id,
                "status": "NOT_AVAILABLE", "reason": "inspect_schema has not run",
                "checked_records": 0, "parse_errors": 0, "full_scan": False,
            }
        return dict(self._inspection_summary)

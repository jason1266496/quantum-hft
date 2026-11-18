"""Bounded streaming inspection of Snapshot JSON; never applies Diff events.

Snapshot is one JSON object, so its full structure is traversed to count levels.
Default inspection validates values and ordering only in each side's bounded
prefix. stream_records validates every yielded level, preserving O(1) book memory.
"""

from __future__ import annotations

import json
from decimal import Decimal

from .base import BaseAdapter, DataFormatError, parse_decimal


CHUNK_CHARACTERS = 8192
MAX_TOKEN_CHARACTERS = 4096
MAX_OBJECT_KEYS = 128
MAX_JSON_DEPTH = 16
REQUIRED_FIELDS = ("lastUpdateId", "bids", "asks")


def _reject_constant(value):
    raise ValueError("non-finite JSON constant: " + value)


class _Tokens:
    """A bounded token reader; no whole snapshot or side array is retained."""

    def __init__(self, handle, file):
        self.handle = handle
        self.file = file
        self.buffer = ""
        self.position = 0
        self.line = 1

    def error(self, message):
        return DataFormatError(self.file, 1, message, physical_line=self.line)

    def peek(self):
        if self.position == len(self.buffer):
            self.buffer = self.handle.read(CHUNK_CHARACTERS)
            self.position = 0
        return self.buffer[self.position:self.position + 1]

    def take(self):
        result = self.peek()
        if result:
            self.position += 1
            if result == "\n":
                self.line += 1
        return result

    def next(self):
        char = self.peek()
        while char and char in " \t\r\n":
            self.take()
            char = self.peek()
        if not char:
            return ("EOF", None)
        if char in "{}[]:,":
            return (self.take(), None)
        pieces = []
        if char == '"':
            pieces.append(self.take())
            escaped = False
            while True:
                char = self.take()
                if not char:
                    raise self.error("unterminated JSON string")
                pieces.append(char)
                if len(pieces) > MAX_TOKEN_CHARACTERS:
                    raise self.error("JSON token exceeds safety limit")
                if char == '"' and not escaped:
                    break
                escaped = char == "\\" and not escaped
        else:
            while char and char not in " \t\r\n{}[]:,":
                pieces.append(self.take())
                if len(pieces) > MAX_TOKEN_CHARACTERS:
                    raise self.error("JSON token exceeds safety limit")
                char = self.peek()
        try:
            value = json.loads(
                "".join(pieces), parse_float=Decimal,
                parse_constant=_reject_constant,
            )
        except (ValueError, RecursionError) as exc:
            raise self.error("invalid JSON scalar: " + str(exc)) from exc
        return ("value", value)

    def expect(self, expected):
        token = self.next()
        if token[0] != expected:
            raise self.error("expected " + repr(expected) + ", got " + repr(token[0]))
        return token[1]

    def skip_value(self, first=None, depth=0):
        """Validate unknown metadata structure with bounded depth/key storage."""
        if depth > MAX_JSON_DEPTH:
            raise self.error("JSON nesting exceeds safety limit")
        token = self.next() if first is None else first
        if token[0] == "value":
            return
        if token[0] == "[":
            token = self.next()
            if token[0] == "]":
                return
            while True:
                self.skip_value(token, depth + 1)
                token = self.next()
                if token[0] == "]":
                    return
                if token[0] != ",":
                    raise self.error("expected comma or array end")
                token = self.next()
        elif token[0] == "{":
            seen = set()
            token = self.next()
            if token[0] == "}":
                return
            while True:
                if token[0] != "value" or not isinstance(token[1], str):
                    raise self.error("object key must be a JSON string")
                if token[1] in seen:
                    raise self.error("duplicate JSON key: " + token[1])
                seen.add(token[1])
                if len(seen) > MAX_OBJECT_KEYS:
                    raise self.error("object key count exceeds safety limit")
                self.expect(":")
                self.skip_value(depth=depth + 1)
                token = self.next()
                if token[0] == "}":
                    return
                if token[0] != ",":
                    raise self.error("expected comma or object end")
                token = self.next()
        else:
            raise self.error("expected a JSON value")


class SnapshotAdapter(BaseAdapter):
    """Read one Snapshot independently; no reconstructed book is created."""

    def __init__(self, registry, source_id):
        super().__init__(registry, source_id)
        if self.source.file_type != "snapshot":
            raise ValueError("SnapshotAdapter requires a registered snapshot source")
        self._inspection_summary = None

    @staticmethod
    def _check_limit(sample_records):
        if sample_records is not None and (
            type(sample_records) is not int or sample_records <= 0
        ):
            raise ValueError("sample_records must be a positive integer or None")

    def _parse(self, sample_records):
        self._check_limit(sample_records)
        self.validate_source()
        with self._open_text() as handle:
            tokens = _Tokens(handle, self.source.absolute_path)
            counts = {"bids": 0, "asks": 0}
            sampled = {"bids": 0, "asks": 0}
            best = {}
            last_update_id = None
            seen = set()
            try:
                tokens.expect("{")
                key_token = tokens.next()
                if key_token[0] == "}":
                    raise tokens.error("missing required fields: lastUpdateId, bids, asks")
                while True:
                    if key_token[0] != "value" or not isinstance(key_token[1], str):
                        raise tokens.error("Snapshot object key must be a JSON string")
                    key = key_token[1]
                    if key in seen:
                        raise tokens.error("duplicate JSON key: " + key)
                    seen.add(key)
                    if len(seen) > MAX_OBJECT_KEYS:
                        raise tokens.error("object key count exceeds safety limit")
                    tokens.expect(":")
                    if key == "lastUpdateId":
                        last_update_id = tokens.expect("value")
                        if type(last_update_id) is not int or last_update_id < 0:
                            raise tokens.error("lastUpdateId must be a nonnegative JSON integer")
                    elif key in counts:
                        tokens.expect("[")
                        level_start = tokens.next()
                        previous_price = None
                        if level_start[0] == "]":
                            raise tokens.error(key + " must contain at least one level")
                        while True:
                            if level_start[0] != "[":
                                raise tokens.error(key + " level must be a price/quantity array")
                            raw_price = tokens.expect("value")
                            tokens.expect(",")
                            raw_quantity = tokens.expect("value")
                            tokens.expect("]")
                            counts[key] += 1
                            for value in (raw_price, raw_quantity):
                                if isinstance(value, bool) or not isinstance(value, (str, int, Decimal)):
                                    raise tokens.error(key + " level must contain decimal-compatible scalars")
                            checked = sample_records is None or counts[key] <= sample_records
                            if checked:
                                prefix = key + "[" + str(counts[key]) + "]"
                                price = parse_decimal(
                                    raw_price, file=self.source.absolute_path, record_index=1,
                                    field=prefix + ".price", physical_line=tokens.line, minimum=0,
                                )
                                quantity = parse_decimal(
                                    raw_quantity, file=self.source.absolute_path, record_index=1,
                                    field=prefix + ".quantity", physical_line=tokens.line, minimum=0,
                                )
                                if price <= 0:
                                    raise tokens.error(prefix + ".price must be positive")
                                if previous_price is not None and (
                                    (key == "bids" and price >= previous_price)
                                    or (key == "asks" and price <= previous_price)
                                ):
                                    raise tokens.error(key + " prices must be strictly ordered")
                                previous_price = price
                                sampled[key] += 1
                                if counts[key] == 1:
                                    best[key] = price
                                yield {
                                    "record_type": "snapshot_level", "record_index": 1,
                                    "source_id": self.source.source_id,
                                    "session_id": self.source.session_id,
                                    "side": key, "level_index": counts[key],
                                    "price": price, "quantity": quantity,
                                }
                            delimiter = tokens.next()
                            if delimiter[0] == "]":
                                break
                            if delimiter[0] != ",":
                                raise tokens.error("expected comma or side array end")
                            level_start = tokens.next()
                    else:
                        tokens.skip_value()
                    delimiter = tokens.next()
                    if delimiter[0] == "}":
                        break
                    if delimiter[0] != ",":
                        raise tokens.error("expected comma or Snapshot object end")
                    key_token = tokens.next()
                missing = sorted(set(REQUIRED_FIELDS) - seen)
                if missing:
                    raise tokens.error("missing required fields: " + ", ".join(missing))
                if tokens.next()[0] != "EOF":
                    raise tokens.error("trailing data after Snapshot JSON")
                if best["bids"] >= best["asks"]:
                    raise tokens.error("crossed or locked Snapshot book")
                yield {
                    "record_type": "snapshot_metadata", "record_index": 1,
                    "source_id": self.source.source_id, "session_id": self.source.session_id,
                    "lastUpdateId": last_update_id,
                    "bid_level_count": counts["bids"], "ask_level_count": counts["asks"],
                    "total_levels_scanned": dict(counts), "sampled_levels": dict(sampled),
                    "event_time_start": None, "event_time_end": None,
                }
            except UnicodeError as exc:
                raise tokens.error("invalid UTF-8: " + str(exc)) from exc

    def stream_records(self):
        """Yield validated levels then final metadata, retaining no whole book.

        Full-consumption validates the complete structure, values, ordering and
        crossed-book rule. Consumers must exhaust the iterator before treating
        its source as schema-validated; metadata is deliberately emitted last.
        """
        yield from self._parse(None)

    def inspect_schema(self, sample_records=100):
        """Count all levels structurally; validate a bounded prefix on each side."""
        self._check_limit(sample_records)
        summary = {
            "source_id": self.source.source_id, "session_id": self.source.session_id,
            "session_id_semantics": "research_registry_alias_not_capture_identity",
            "adapter": type(self).__name__, "file_type": "snapshot", "status": "PASS",
            "checked_records": 0, "parse_errors": 0,
            "full_scan": sample_records is None, "sample_limit_per_side": sample_records,
            "schema_scope": (
                "FULL_STRUCTURAL_AND_VALUE_SCAN" if sample_records is None
                else "FULL_STRUCTURAL_SCAN_WITH_BOUNDED_VALUE_SAMPLE"
            ),
            "required_fields": list(REQUIRED_FIELDS), "extra_fields": "bounded_structural_validation",
            "total_levels_scanned": {"bids": 0, "asks": 0},
            "sampled_levels": {"bids": 0, "asks": 0},
            "unchecked_value_count": {"bids": 0, "asks": 0},
            "unexamined_values": "NOT_CHECKED",
            "ordering_scope": "all_levels" if sample_records is None else "sampled_prefix_per_side",
            "crossed_book_scope": "first_bid_and_first_ask",
            "numeric_representation": "finite_exact_Decimal_price_quantity",
            "event_time_start_observed": None, "event_time_end_observed": None,
            "timestamp_policy": {
                "event_time": "NOT_AVAILABLE",
                "replay_time_substituted": False, "local_receive_time": "NOT_AVAILABLE",
                "cross_session_merge": False,
            },
            "diff_events_applied": False, "order_book_reconstructed": False,
            "derived_features": False, "future_labels": False,
        }
        self._inspection_summary = summary
        records = self._parse(sample_records)
        try:
            for record in records:
                if record["record_type"] == "snapshot_metadata":
                    summary.update({
                        field: record[field] for field in (
                            "lastUpdateId", "bid_level_count", "ask_level_count",
                            "total_levels_scanned", "sampled_levels",
                        )
                    })
                    summary["checked_records"] = 1
            summary["unchecked_value_count"] = {
                side: summary["total_levels_scanned"][side] - summary["sampled_levels"][side]
                for side in ("bids", "asks")
            }
            if not any(summary["unchecked_value_count"].values()):
                summary["unexamined_values"] = "NONE"
        except DataFormatError:
            summary["status"] = "FAIL"
            summary["parse_errors"] += 1
            raise
        finally:
            records.close()
        return dict(summary)

    def summarize(self):
        """Return cached aggregate inspection metadata without reopening input."""
        if self._inspection_summary is None:
            return {
                "source_id": self.source.source_id, "session_id": self.source.session_id,
                "status": "NOT_AVAILABLE", "reason": "inspect_schema has not run",
                "checked_records": 0, "parse_errors": 0, "full_scan": False,
            }
        return dict(self._inspection_summary)


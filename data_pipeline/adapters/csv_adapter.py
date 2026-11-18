"""Read-only, session-isolated validation of the ten-column HFT CSV contract."""

from __future__ import annotations

import csv
from itertools import islice

from .base import BaseAdapter, DataFormatError, parse_decimal, parse_integer


REQUIRED_COLUMNS = (
    "local_timestamp_us", "event_time_ms", "update_id", "best_bid", "best_ask",
    "mid_price", "spread", "bid_volume_5", "ask_volume_5", "obi_5",
)
MAX_LINE_BYTES = 1_048_576
TIMESTAMP_POLICY = {
    "order_field": "event_time_ms",
    "event_time_role": "offline_order_alignment_and_split_metadata_only",
    "local_timestamp_field": "local_timestamp_us",
    "local_timestamp_is_receive_time": False,
    "local_timestamp_semantics": "receive_time_not_established",
    "local_timestamp_allowed_for_network_latency": False,
    "local_timestamp_allowed_for_tick_to_trade": False,
    "local_timestamp_allowed_for_model_feature": False,
    "cross_session_merge": False,
}


class CSVAdapter(BaseAdapter):
    """Stream one registered CSV without merging sessions or deriving features."""

    def __init__(self, registry, source_id):
        super().__init__(registry, source_id)
        if self.source.file_type != "csv":
            raise ValueError("CSVAdapter requires a registered csv source")
        self._inspection_summary = None

    def _error(self, index, message, line=None):
        return DataFormatError(
            self.source.absolute_path, index, message, physical_line=line
        )

    def _readline(self, handle, index, physical_line):
        line = handle.readline(MAX_LINE_BYTES + 1)
        if len(line) > MAX_LINE_BYTES:
            raise self._error(index, "physical line exceeds safety limit", physical_line)
        try:
            return line.decode("utf-8", errors="strict")
        except UnicodeError as exc:
            raise self._error(index, "invalid UTF-8", physical_line) from exc

    def _parse_line(self, line, index, physical_line):
        if not line.strip():
            raise self._error(index, "empty CSV row", physical_line)
        try:
            parsed = next(csv.reader([line], strict=True))
        except (csv.Error, StopIteration) as exc:
            raise self._error(index, "CSV parse error: " + str(exc), physical_line) from exc
        return parsed

    def _iter_records(self):
        """Yield precise values plus source/session metadata; fail on the first bad row."""
        self.validate_source()
        with self._open_binary() as handle:
            header_line = self._readline(handle, 0, 1)
            if not header_line:
                raise self._error(0, "missing CSV header", 1)
            header = self._parse_line(header_line, 0, 1)
            if len(header) != len(set(header)):
                raise self._error(0, "duplicate CSV header fields", 1)
            missing = sorted(set(REQUIRED_COLUMNS) - set(header))
            unexpected = sorted(set(header) - set(REQUIRED_COLUMNS))
            if missing or unexpected:
                raise self._error(
                    0, "CSV header mismatch; missing=" + repr(missing)
                    + "; unexpected=" + repr(unexpected), 1
                )
            index = 0
            while True:
                physical_line = index + 2
                line = self._readline(handle, index + 1, physical_line)
                if not line:
                    break
                index += 1
                fields = self._parse_line(line, index, physical_line)
                if len(fields) != len(header):
                    raise self._error(index, "CSV field count does not match header", physical_line)
                raw = dict(zip(header, fields))
                record = {}
                for field in REQUIRED_COLUMNS:
                    value = raw[field]
                    parser = parse_integer if field in REQUIRED_COLUMNS[:3] else parse_decimal
                    kwargs = {
                        "file": self.source.absolute_path, "record_index": index,
                        "field": field, "physical_line": physical_line,
                    }
                    if field in REQUIRED_COLUMNS[:3] or field in (
                        "spread", "bid_volume_5", "ask_volume_5"
                    ):
                        kwargs["minimum"] = 0
                    record[field] = parser(value, **kwargs)
                for field in ("best_bid", "best_ask", "mid_price"):
                    if record[field] <= 0:
                        raise self._error(index, field + " must be positive", physical_line)
                if record["best_bid"] > record["best_ask"]:
                    raise self._error(index, "crossed best bid/ask", physical_line)
                if not -1 <= record["obi_5"] <= 1:
                    raise self._error(index, "obi_5 must be between -1 and 1", physical_line)
                record.update(
                    record_index=index, physical_line=physical_line,
                    source_id=self.source.source_id, session_id=self.source.session_id,
                )
                yield record

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
        """Inspect at most sample_records; None explicitly requests a streaming full scan."""
        if sample_records is not None and (
            type(sample_records) is not int or sample_records <= 0
        ):
            raise ValueError("sample_records must be a positive integer or None")
        summary = {
            "source_id": self.source.source_id,
            "session_id": self.source.session_id,
            "session_id_semantics": "research_registry_alias_not_capture_identity",
            "adapter": type(self).__name__,
            "file_type": "csv",
            "status": "PASS",
            "checked_records": 0,
            "parse_errors": 0,
            "full_scan": sample_records is None,
            "sample_limit": sample_records,
            "schema_scope": (
                "all_records" if sample_records is None else "header_and_at_most_sample_limit_records"
            ),
            "required_columns": list(REQUIRED_COLUMNS),
            "numeric_representation": "nonnegative_int_ids_and_finite_Decimal_values",
            "event_time_start_observed": None,
            "event_time_end_observed": None,
            "timestamp_policy": dict(TIMESTAMP_POLICY),
            "derived_features": False,
            "future_labels": False,
            "obi_recomputed": False,
        }
        records = self.stream_records()
        self._inspection_summary = summary
        try:
            selected = records if sample_records is None else islice(records, sample_records)
            for record in selected:
                if summary["checked_records"] == 0:
                    summary["event_time_start_observed"] = record["event_time_ms"]
                summary["event_time_end_observed"] = record["event_time_ms"]
                summary["checked_records"] += 1
            if not summary["checked_records"]:
                raise self._error(1, "CSV has a header but no data rows", 2)
        except DataFormatError:
            summary["status"] = "FAIL"
            summary["parse_errors"] += 1
            raise
        finally:
            records.close()
        return summary

    def summarize(self):
        """Return the inspection summary without an implicit scan."""
        self._ensure_open()
        if self._inspection_summary is None:
            return {
                "source_id": self.source.source_id, "session_id": self.source.session_id,
                "status": "NOT_AVAILABLE", "reason": "inspect_schema has not run",
                "checked_records": 0, "parse_errors": 0, "full_scan": False,
            }
        return dict(self._inspection_summary)

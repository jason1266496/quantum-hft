"""Synthetic-only CSV contract tests; temporary inputs remain under tests/."""

import json
import os
from pathlib import Path
from decimal import Decimal
import tempfile
import unittest
from unittest import mock

from data_pipeline.adapters.base import DataFormatError
from data_pipeline.adapters.csv_adapter import CSVAdapter, REQUIRED_COLUMNS
from data_pipeline.registry import DatasetRegistry, SourceValidationError
from tests.phase2a_helpers import make_registry_fixture


HEADER = ",".join(REQUIRED_COLUMNS) + "\n"
ROW = "10,1000,42,100.10,100.20,100.15,0.10,2,2,0.75\n"


class CSVAdapterTests(unittest.TestCase):
    def fixture(self, text=HEADER + ROW, payloads=None):
        temporary = tempfile.TemporaryDirectory(prefix="phase2a_csv_", dir=Path(__file__).parent)
        self.addCleanup(temporary.cleanup)
        config, root = make_registry_fixture(
            temporary.name, payloads or [("sample.csv", "csv", text)]
        )
        registry = DatasetRegistry(config, allowed_roots=(root,), require_nine_sources=False)
        return registry, root

    def adapter(self, text=HEADER + ROW):
        registry, _ = self.fixture(text)
        return CSVAdapter(registry, "sample")

    def assert_bad(self, text, record=1, physical_line=2):
        adapter = self.adapter(text)
        with self.assertRaises(DataFormatError) as error:
            list(adapter.stream_records())
        self.assertEqual(error.exception.record_index, record)
        self.assertEqual(error.exception.physical_line, physical_line)
        self.assertIn("sample.csv", str(error.exception))
        return error.exception

    def test_valid_schema_and_exact_decimal(self):
        adapter = self.adapter()
        records = list(adapter.stream_records())
        self.assertEqual(len(records), 1)
        row = records[0]
        self.assertEqual(row["best_bid"], Decimal("100.10"))
        self.assertIs(type(row["event_time_ms"]), int)
        self.assertEqual(row["session_id"], "synthetic_sample")
        self.assertEqual(row["record_index"], 1)
        self.assertEqual(row["physical_line"], 2)

    def test_schema_inspection_is_json_serializable(self):
        result = self.adapter().inspect_schema()
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["checked_records"], 1)
        self.assertFalse(result["full_scan"])
        self.assertEqual(result["parse_errors"], 0)
        json.dumps(result)

    def test_missing_required_header_field(self):
        self.assert_bad(",".join(REQUIRED_COLUMNS[:-1]) + "\n" + ROW, 0, 1)

    def test_duplicate_header_field(self):
        self.assert_bad(HEADER.strip() + ",event_time_ms\n" + ROW, 0, 1)

    def test_unexpected_header_field(self):
        self.assert_bad(HEADER.strip() + ",receive_time\n" + ROW, 0, 1)

    def test_empty_file(self):
        self.assert_bad("", 0, 1)

    def test_header_without_records_fails_inspection(self):
        with self.assertRaises(DataFormatError):
            self.adapter(HEADER).inspect_schema()

    def test_blank_row_is_not_skipped(self):
        self.assert_bad(HEADER + "\n" + ROW)

    def test_bad_column_count(self):
        self.assert_bad(HEADER + "10,1000,42\n")

    def test_malformed_csv_quote(self):
        self.assert_bad(HEADER + '"unterminated\n')

    def test_invalid_integer_types(self):
        for value in ("1.2", "1e3", "NaN", "-1", "True", ""):
            with self.subTest(value=value):
                self.assert_bad(HEADER + ROW.replace("10,", value + ",", 1))

    def test_nonfinite_or_missing_decimal(self):
        for value in ("NaN", "Infinity", "-Infinity", ""):
            with self.subTest(value=value):
                self.assert_bad(HEADER + ROW.replace("100.10", value))

    def test_illegal_book_values(self):
        for old, new in (("100.10", "100.30"), ("100.10", "0"), ("2,2", "-1,2"), ("0.75", "1.1")):
            with self.subTest(value=new):
                self.assert_bad(HEADER + ROW.replace(old, new))

    def test_existing_obi_is_preserved_without_recomputation(self):
        # Balanced aggregate quantities deliberately have an arbitrary valid OBI.
        record = next(self.adapter().stream_records())
        self.assertEqual(record["obi_5"], Decimal("0.75"))
        self.assertFalse(self.adapter().inspect_schema()["obi_recomputed"])

    def test_local_timestamp_never_claims_receive_or_latency(self):
        adapter = self.adapter()
        record = next(adapter.stream_records())
        self.assertEqual(record["local_timestamp_us"], 10)
        self.assertNotIn("latency", record)
        policy = adapter.inspect_schema()["timestamp_policy"]
        self.assertFalse(policy["local_timestamp_is_receive_time"])
        self.assertFalse(policy["local_timestamp_allowed_for_network_latency"])
        self.assertFalse(policy["local_timestamp_allowed_for_model_feature"])

    def test_sample_does_not_parse_record_after_limit(self):
        adapter = self.adapter(HEADER + ROW * 100 + "bad,row\n")
        self.assertEqual(adapter.inspect_schema(100)["checked_records"], 100)
        with self.assertRaises(DataFormatError) as error:
            adapter.inspect_schema(None)
        self.assertEqual(error.exception.record_index, 101)
        self.assertEqual(adapter.summarize()["checked_records"], 100)
        self.assertEqual(adapter.summarize()["parse_errors"], 1)
        self.assertEqual(adapter.summarize()["status"], "FAIL")

    def test_sessions_are_never_merged(self):
        registry, _ = self.fixture(payloads=[
            ("first.csv", "csv", HEADER + ROW),
            ("second.csv", "csv", HEADER + ROW),
        ])
        first = list(CSVAdapter(registry, "first").stream_records())
        second = list(CSVAdapter(registry, "second").stream_records())
        self.assertEqual(len(first), 1)
        self.assertEqual(len(second), 1)
        self.assertNotEqual(first[0]["session_id"], second[0]["session_id"])
        self.assertNotEqual(first[0]["source_id"], second[0]["source_id"])

    def test_input_opens_have_no_write_flags_or_metadata_changes(self):
        adapter = self.adapter()
        path = Path(adapter.source.absolute_path)
        before = path.stat()
        names_before = sorted(p.name for p in path.parent.iterdir())
        opened_flags = []
        original_open = os.open

        def checked_open(path_arg, flags, *args, **kwargs):
            opened_flags.append(flags)
            self.assertFalse(flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND))
            return original_open(path_arg, flags, *args, **kwargs)

        with mock.patch("os.open", side_effect=checked_open):
            adapter.inspect_schema()
        self.assertTrue(opened_flags)
        after = path.stat()
        self.assertEqual(
            (before.st_size, before.st_mtime_ns, before.st_ctime_ns, before.st_mode),
            (after.st_size, after.st_mtime_ns, after.st_ctime_ns, after.st_mode),
        )
        self.assertEqual(names_before, sorted(p.name for p in path.parent.iterdir()))

    def test_summarize_never_triggers_another_scan(self):
        adapter = self.adapter()
        self.assertEqual(adapter.summarize()["status"], "NOT_AVAILABLE")
        result = adapter.inspect_schema()
        with mock.patch.object(adapter, "_open_binary", side_effect=AssertionError("unexpected scan")):
            self.assertEqual(adapter.summarize(), result)

    def test_hash_mismatch_prevents_record_access(self):
        registry, _ = self.fixture()
        source = registry.get("sample")
        Path(source.absolute_path).write_text(HEADER + ROW.replace("42,", "43,"), encoding="utf-8")
        with self.assertRaises(SourceValidationError):
            next(CSVAdapter(registry, "sample").stream_records())

    def test_closed_adapter_rejects_stream(self):
        adapter = self.adapter()
        adapter.close()
        with self.assertRaises(SourceValidationError):
            next(adapter.stream_records())

    def test_bad_sample_limit(self):
        for value in (0, -1, True, "100"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.adapter().inspect_schema(value)

    def test_bounded_physical_line(self):
        with mock.patch("data_pipeline.adapters.csv_adapter.MAX_LINE_BYTES", 256):
            self.assert_bad(HEADER + "1" * 257 + "\n")

    def test_invalid_utf8_reports_location(self):
        self.assert_bad((HEADER + ROW).encode("utf-8") + b"\xff\n", 2, 3)

    def test_stream_limit_returns_only_requested_records(self):
        adapter = self.adapter(HEADER + ROW * 2)
        self.assertEqual(len(list(adapter.stream_records(limit=1))), 1)


if __name__ == "__main__":
    unittest.main()

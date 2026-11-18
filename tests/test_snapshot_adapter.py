"""Artificial Snapshot fixtures only; temporary files remain inside tests/."""

import json
from decimal import Decimal
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from data_pipeline.adapters.base import DataFormatError
from data_pipeline.adapters.snapshot_adapter import SnapshotAdapter
from data_pipeline.registry import DatasetRegistry, SourceValidationError
from tests.phase2a_helpers import make_registry_fixture


GOOD = {
    "lastUpdateId": 7,
    "bids": [["100.00", "2.50"], ["99.00", "0"]],
    "asks": [["101.00", "1.25"], ["102.00", "3"]],
}


class SnapshotAdapterTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(
            prefix="snapshot_fixture_", dir=Path(__file__).parent
        )
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name)
        self.case_count = 0

    def adapter(self, payload=None, filename="snapshot.json", kind="snapshot"):
        self.case_count += 1
        case = self.base / str(self.case_count)
        case.mkdir()
        if payload is None:
            payload = json.dumps(GOOD)
        elif isinstance(payload, dict):
            payload = json.dumps(payload)
        config, root = make_registry_fixture(case, [(filename, kind, payload)])
        registry = DatasetRegistry(
            config, allowed_roots=(root,), require_nine_sources=False
        )
        return SnapshotAdapter(registry, Path(filename).stem)

    def assert_invalid(self, payload, message):
        adapter = self.adapter(payload)
        with self.assertRaisesRegex(DataFormatError, message) as caught:
            adapter.inspect_schema()
        self.assertIn(adapter.source.absolute_path, str(caught.exception))
        self.assertEqual(caught.exception.record_index, 1)
        self.assertIsNotNone(caught.exception.physical_line)
        self.assertEqual(adapter.summarize()["status"], "FAIL")

    def test_normal_snapshot_schema_and_counts(self):
        adapter = self.adapter()
        summary = adapter.inspect_schema()
        self.assertEqual(summary["status"], "PASS")
        self.assertEqual(summary["lastUpdateId"], 7)
        self.assertEqual(summary["total_levels_scanned"], {"bids": 2, "asks": 2})
        self.assertEqual(summary["sampled_levels"], {"bids": 2, "asks": 2})
        self.assertEqual(summary["checked_records"], 1)
        self.assertIsNone(summary["event_time_start_observed"])
        self.assertFalse(summary["order_book_reconstructed"])
        self.assertFalse(summary["diff_events_applied"])

    def test_stream_yields_levels_and_final_metadata(self):
        rows = list(self.adapter().stream_records())
        self.assertEqual(len(rows), 5)
        self.assertEqual(rows[-1]["record_type"], "snapshot_metadata")
        self.assertEqual(rows[-1]["lastUpdateId"], 7)
        self.assertEqual(rows[0]["price"], Decimal("100.00"))
        self.assertEqual(rows[0]["quantity"], Decimal("2.50"))
        self.assertEqual({row["session_id"] for row in rows}, {"synthetic_snapshot"})

    def test_last_update_id_after_sides_is_supported(self):
        payload = '{"asks":[["101","1"]],"bids":[["100","1"]],"lastUpdateId":7}'
        self.assertEqual(self.adapter(payload).inspect_schema()["lastUpdateId"], 7)

    def test_missing_last_update_id(self):
        self.assert_invalid({"bids": GOOD["bids"], "asks": GOOD["asks"]}, "missing required")

    def test_id_must_be_json_integer_not_bool_float_or_string(self):
        for value in (True, 7.0, "7", -1):
            with self.subTest(value=value):
                self.assert_invalid(dict(GOOD, lastUpdateId=value), "nonnegative JSON integer")

    def test_crossed_book(self):
        self.assert_invalid(dict(GOOD, asks=[["99", "1"]]), "crossed")

    def test_locked_book(self):
        self.assert_invalid(dict(GOOD, asks=[["100", "1"]]), "locked")

    def test_bids_must_descend_without_duplicate_prices(self):
        for bids in ([["99", "1"], ["100", "1"]], [["100", "1"], ["100", "2"]]):
            with self.subTest(bids=bids):
                self.assert_invalid(dict(GOOD, bids=bids), "strictly ordered")

    def test_asks_must_ascend(self):
        self.assert_invalid(dict(GOOD, asks=[["102", "1"], ["101", "1"]]), "strictly ordered")

    def test_quantity_finite_and_nonnegative(self):
        for quantity in ("-1", "NaN", "Infinity", "bad", True):
            with self.subTest(quantity=quantity):
                self.assert_invalid(dict(GOOD, bids=[["100", quantity]]), "decimal|finite")

    def test_price_positive(self):
        self.assert_invalid(dict(GOOD, bids=[["0", "1"]]), "positive")

    def test_level_must_be_exact_pair(self):
        for bids in ([["100"]], [["100", "1", "extra"]], ["100"], {"100": "1"}):
            with self.subTest(bids=bids):
                self.assert_invalid(dict(GOOD, bids=bids), "expected|level")

    def test_empty_side_rejected(self):
        self.assert_invalid(dict(GOOD, bids=[]), "at least one level")

    def test_duplicate_top_level_key_rejected(self):
        payload = '{"lastUpdateId":7,"lastUpdateId":8,"bids":[["100","1"]],"asks":[["101","1"]]}'
        self.assert_invalid(payload, "duplicate JSON key")

    def test_trailing_garbage_rejected(self):
        self.assert_invalid(json.dumps(GOOD) + "{}","trailing data")

    def test_trailing_comma_rejected(self):
        payload = '{"lastUpdateId":7,"bids":[["100","1"],],"asks":[["101","1"]]}'
        self.assert_invalid(payload, "level")

    def test_bounded_token_safety_limit(self):
        with patch("data_pipeline.adapters.snapshot_adapter.MAX_TOKEN_CHARACTERS", 32):
            self.assert_invalid(dict(GOOD, bids=[["1" * 40, "1"]]), "safety limit")

    def test_chunk_boundaries_inside_strings_and_numbers(self):
        with patch("data_pipeline.adapters.snapshot_adapter.CHUNK_CHARACTERS", 3):
            result = self.adapter().inspect_schema()
        self.assertEqual(result["status"], "PASS")

    def test_numeric_json_values_retain_decimal_precision(self):
        payload = '{"lastUpdateId":7,"bids":[[100.000000000000000001,1.5]],"asks":[[101,2]]}'
        rows = list(self.adapter(payload).stream_records())
        self.assertEqual(rows[0]["price"], Decimal("100.000000000000000001"))

    def test_unknown_metadata_is_structurally_validated(self):
        summary = self.adapter(dict(GOOD, metadata={"note": ["test", {"value": 1}]})).inspect_schema()
        self.assertEqual(summary["status"], "PASS")
        bad = json.dumps(GOOD)[:-1] + ',"meta":{"x":1,"x":2}}'
        self.assert_invalid(bad, "duplicate JSON key")

    def test_invalid_utf8_reports_position(self):
        self.assert_invalid(b'{"lastUpdateId":7,"bids":\xff}', "invalid UTF-8")

    def test_sampling_records_unchecked_values_explicitly(self):
        payload = dict(GOOD, bids=[["100", "1"], ["bad", "-2"]])
        adapter = self.adapter(payload)
        summary = adapter.inspect_schema(sample_records=1)
        self.assertEqual(summary["status"], "PASS")
        self.assertEqual(summary["sampled_levels"], {"bids": 1, "asks": 1})
        self.assertEqual(summary["total_levels_scanned"], {"bids": 2, "asks": 2})
        self.assertEqual(summary["unchecked_value_count"], {"bids": 1, "asks": 1})
        self.assertEqual(summary["unexamined_values"], "NOT_CHECKED")
        self.assertEqual(summary["schema_scope"], "FULL_STRUCTURAL_SCAN_WITH_BOUNDED_VALUE_SAMPLE")
        with self.assertRaises(DataFormatError):
            adapter.inspect_schema(sample_records=None)

    def test_structure_outside_value_sample_still_checked(self):
        adapter = self.adapter(dict(GOOD, bids=[["100", "1"], ["99"]]))
        with self.assertRaisesRegex(DataFormatError, "expected"):
            adapter.inspect_schema(sample_records=1)
        self.assertEqual(adapter.summarize()["status"], "FAIL")

    def test_invalid_sample_limits(self):
        adapter = self.adapter()
        for limit in (0, -1, True, 1.5):
            with self.subTest(limit=limit), self.assertRaises(ValueError):
                adapter.inspect_schema(sample_records=limit)

    def test_summarize_does_not_read_input(self):
        adapter = self.adapter()
        self.assertEqual(adapter.summarize()["status"], "NOT_AVAILABLE")
        expected = adapter.inspect_schema()
        with patch.object(adapter, "_open_text", side_effect=AssertionError("unexpected read")):
            self.assertEqual(adapter.summarize(), expected)

    def test_read_only_flags_and_input_content_metadata_unchanged(self):
        import os
        adapter = self.adapter()
        source = Path(adapter.source.absolute_path)
        before_content = source.read_bytes()
        before = source.stat()
        real_open = os.open
        calls = []

        def guarded_open(path, flags, *args, **kwargs):
            calls.append(flags)
            self.assertEqual(flags & os.O_ACCMODE, os.O_RDONLY)
            self.assertFalse(flags & (os.O_CREAT | os.O_TRUNC | os.O_APPEND))
            return real_open(path, flags, *args, **kwargs)

        with patch("data_pipeline.adapters.base.os.open", side_effect=guarded_open):
            adapter.inspect_schema()
        after = source.stat()
        self.assertTrue(calls)
        self.assertEqual(source.read_bytes(), before_content)
        self.assertEqual(
            (before.st_mode, before.st_size, before.st_mtime_ns, before.st_ctime_ns),
            (after.st_mode, after.st_size, after.st_mtime_ns, after.st_ctime_ns),
        )
        self.assertEqual(sorted(p.name for p in source.parent.iterdir()), ["snapshot.json"])

    def test_hash_mismatch_stops_before_schema(self):
        adapter = self.adapter()
        source = Path(adapter.source.absolute_path)
        source.write_text(json.dumps(dict(GOOD, lastUpdateId=8)), encoding="utf-8")
        with self.assertRaises(SourceValidationError):
            adapter.inspect_schema()

    def test_close_blocks_further_reads(self):
        adapter = self.adapter()
        adapter.close()
        with self.assertRaises(SourceValidationError):
            next(adapter.stream_records())

    def test_sessions_stay_separate(self):
        first = self.adapter(filename="first.json")
        second = self.adapter(filename="second.json")
        self.assertNotEqual(first.source.session_id, second.source.session_id)
        a = list(first.stream_records())
        b = list(second.stream_records())
        self.assertEqual({row["session_id"] for row in a}, {first.source.session_id})
        self.assertEqual({row["session_id"] for row in b}, {second.source.session_id})


if __name__ == "__main__":
    unittest.main()


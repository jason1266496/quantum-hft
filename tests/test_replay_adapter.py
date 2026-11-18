"""Artificial Replay JSONL tests; no HFT data, book application, or OBI."""

import json
from contextlib import contextmanager
from decimal import Decimal
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from data_pipeline.adapters.base import DataFormatError
from data_pipeline.adapters.replay_adapter import ReplayAdapter, MAX_LINE_BYTES, SCHEMA_VARIANT
from data_pipeline.registry import DatasetRegistry, SourceValidationError
from tests.phase2a_helpers import make_registry_fixture


EVENT = {
    "eventTime": 1000, "firstUpdateId": 42, "finalUpdateId": 43,
    "bids": [{"price": 100.1, "quantity": 2.0}, {"price": 100.0, "quantity": 0.0}],
    "asks": [{"price": 100.2, "quantity": 3.0}],
}

# Two different hand-written events, one confirmed capture schema. These are not
# source records or values copied from either production Replay file.
REPLAY_1000_EQUIVALENT = (
    '{"eventTime":2000,"firstUpdateId":10,"finalUpdateId":11,'
    '"bids":[{"price":7.25,"quantity":2.0}],'
    '"asks":[{"price":7.5,"quantity":0.0}]}\n'
)
REPLAY_50000_EQUIVALENT = (
    '{"eventTime":3000,"firstUpdateId":20,"finalUpdateId":22,'
    '"bids":[{"price":12.125,"quantity":0.5}],'
    '"asks":[{"price":12.25,"quantity":4.0}]}\n'
)


def line(event=None):
    return json.dumps(EVENT if event is None else event) + "\n"


class ReplayAdapterTests(unittest.TestCase):
    def fixture(self, text=None, payloads=None):
        temporary = tempfile.TemporaryDirectory(prefix="phase2a_replay_", dir=Path(__file__).parent)
        self.addCleanup(temporary.cleanup)
        config, root = make_registry_fixture(
            temporary.name, payloads or [("events.jsonl", "replay", line() if text is None else text)]
        )
        return DatasetRegistry(config, allowed_roots=(root,), require_nine_sources=False), root

    def adapter(self, text=None):
        registry, _ = self.fixture(text)
        return ReplayAdapter(registry, "events")

    def assert_bad(self, text, record=1):
        with self.assertRaises(DataFormatError) as error:
            list(self.adapter(text).stream_records())
        self.assertEqual(error.exception.record_index, record)
        self.assertEqual(error.exception.physical_line, record)
        self.assertIn("events.jsonl", str(error.exception))
        self.assertEqual(error.exception.source_id, "events")
        self.assertIn("source_id=events", str(error.exception))
        self.assertIn("record_index=" + str(record), str(error.exception))
        self.assertIn("side=", str(error.exception))
        self.assertIn("update_index=", str(error.exception))
        self.assertIn("raw_summary=", str(error.exception))
        self.assertLessEqual(len(error.exception.safe_summary), 192)
        return error.exception

    def test_normal_event_exact_decimal_and_update_counts(self):
        record = next(self.adapter().stream_records())
        self.assertEqual(record["eventTime"], 1000)
        self.assertEqual(record["firstUpdateId"], 42)
        self.assertEqual(record["finalUpdateId"], 43)
        self.assertEqual(record["bid_update_count"], 2)
        self.assertEqual(record["ask_update_count"], 1)
        self.assertEqual(record["bids"][0], (Decimal("100.10"), Decimal("2")))
        self.assertEqual(record["record_index"], 1)
        self.assertEqual(record["session_id"], "synthetic_events")

    def test_zero_quantity_is_retained_without_applying_deletion(self):
        record = next(self.adapter().stream_records())
        self.assertEqual(record["bids"][1][1], Decimal(0))
        self.assertEqual(record["bid_update_count"], 2)
        self.assertNotIn("order_book", record)
        self.assertNotIn("obi", record)

    def test_json_damage_has_record_location(self):
        self.assert_bad(line() + "{broken\n", record=2)

    def test_required_ids_and_event_time(self):
        for field in ("eventTime", "firstUpdateId", "finalUpdateId"):
            event = dict(EVENT)
            event.pop(field)
            with self.subTest(field=field):
                self.assert_bad(line(event))

    def test_json_ids_reject_bool_float_string_negative(self):
        for field in ("eventTime", "firstUpdateId", "finalUpdateId"):
            for value in (True, 42.0, "42", -1):
                event = dict(EVENT, **{field: value})
                with self.subTest(field=field, value=value):
                    self.assert_bad(line(event))

    def test_update_id_range_must_not_reverse(self):
        self.assert_bad(line(dict(EVENT, firstUpdateId=44)))

    def test_side_schema_requires_arrays_of_objects(self):
        for value in ({}, None, [1], [[100]], [[100, 2]], [[100, 2, 3]]):
            with self.subTest(value=value):
                self.assert_bad(line(dict(EVENT, bids=value)))

    def test_missing_side(self):
        event = dict(EVENT)
        event.pop("asks")
        self.assert_bad(line(event))

    def test_bad_price_and_quantity(self):
        for value in [{"price": 0, "quantity": 1}, {"price": -1, "quantity": 1},
                      {"price": 100, "quantity": -1}, {"price": True, "quantity": 1},
                      {"price": "NaN", "quantity": 1}, {"price": 1, "quantity": "Infinity"}]:
            with self.subTest(value=value):
                self.assert_bad(line(dict(EVENT, bids=[value])))

    def test_duplicate_json_keys_are_rejected(self):
        self.assert_bad('{"eventTime":1000,' + line().lstrip("{"))

    def test_nonfinite_json_constants_are_rejected(self):
        for value in ("NaN", "Infinity", "-Infinity"):
            with self.subTest(value=value):
                self.assert_bad(line().replace("100.1", value, 1))

    def test_blank_records_are_not_skipped(self):
        self.assert_bad(line() + "\n" + line(), record=2)

    def test_root_must_be_object(self):
        self.assert_bad("[]\n")

    def test_empty_replay_fails_inspection(self):
        with self.assertRaises(DataFormatError):
            self.adapter("").inspect_schema()

    def test_sample_summary_is_json_serializable(self):
        result = self.adapter().inspect_schema()
        self.assertEqual(result["checked_records"], 1)
        self.assertEqual(result["bid_updates_checked"], 2)
        self.assertEqual(result["parse_errors"], 0)
        self.assertFalse(result["snapshot_applied"])
        self.assertFalse(result["order_book_updated"])
        self.assertFalse(result["obi_computed"])
        self.assertFalse(result["full_scan"])
        self.assertEqual(result["schema_variant"], SCHEMA_VARIANT)
        self.assertEqual(result["update_schema"]["item"], "object")
        self.assertEqual(result["update_schema"]["value_type"], "JSON_number")
        json.dumps(result)

    def test_sample_stops_without_parsing_next_event(self):
        adapter = self.adapter(line() * 100 + "{bad\n")
        self.assertEqual(adapter.inspect_schema(100)["checked_records"], 100)
        with self.assertRaises(DataFormatError) as error:
            adapter.inspect_schema(None)
        self.assertEqual(error.exception.record_index, 101)
        self.assertEqual(adapter.summarize()["status"], "FAIL")
        self.assertEqual(adapter.summarize()["parse_errors"], 1)

    def test_sessions_stay_separate(self):
        registry, _ = self.fixture(payloads=[
            ("first.jsonl", "replay", line()), ("second.jsonl", "replay", line()),
        ])
        first = next(ReplayAdapter(registry, "first").stream_records())
        second = next(ReplayAdapter(registry, "second").stream_records())
        self.assertNotEqual(first["session_id"], second["session_id"])
        self.assertNotEqual(first["source_id"], second["source_id"])

    def test_summarize_does_not_rescan(self):
        adapter = self.adapter()
        self.assertEqual(adapter.summarize()["status"], "NOT_AVAILABLE")
        result = adapter.inspect_schema()
        with mock.patch.object(adapter, "_open_binary", side_effect=AssertionError("unexpected scan")):
            self.assertEqual(adapter.summarize(), result)

    def test_hash_mismatch_stops_before_json_parsing(self):
        registry, _ = self.fixture()
        path = Path(registry.get("events").absolute_path)
        path.write_text(line().replace("1000", "1001"), encoding="utf-8")
        with self.assertRaises(SourceValidationError):
            next(ReplayAdapter(registry, "events").stream_records())

    def test_input_file_and_directory_remain_unchanged(self):
        adapter = self.adapter()
        path = Path(adapter.source.absolute_path)
        before = path.stat()
        before_bytes = path.read_bytes()
        before_names = sorted(p.name for p in path.parent.iterdir())
        adapter.inspect_schema()
        after = path.stat()
        self.assertEqual(path.read_bytes(), before_bytes)
        self.assertEqual(before_names, sorted(p.name for p in path.parent.iterdir()))
        self.assertEqual(
            (before.st_size, before.st_mtime_ns, before.st_ctime_ns, before.st_mode),
            (after.st_size, after.st_mtime_ns, after.st_ctime_ns, after.st_mode),
        )

    def test_line_size_is_bounded(self):
        with mock.patch("data_pipeline.adapters.replay_adapter.MAX_LINE_BYTES", 128):
            self.assert_bad("x" * 129 + "\n")

    def test_closed_adapter_rejects_stream(self):
        adapter = self.adapter()
        adapter.close()
        with self.assertRaises(SourceValidationError):
            next(adapter.stream_records())

    def test_stream_limit_returns_only_requested_records(self):
        self.assertEqual(len(list(self.adapter(line() * 2).stream_records(limit=1))), 1)

    def test_artificial_replay_1000_equivalent_schema(self):
        record = next(self.adapter(REPLAY_1000_EQUIVALENT).stream_records())
        self.assertEqual(record["schema_variant"], SCHEMA_VARIANT)
        self.assertEqual(record["bids"], ((Decimal("7.25"), Decimal("2.0")),))
        self.assertEqual(record["asks"], ((Decimal("7.5"), Decimal("0.0")),))

    def test_artificial_replay_50000_equivalent_same_schema(self):
        record = next(self.adapter(REPLAY_50000_EQUIVALENT).stream_records())
        self.assertEqual(record["schema_variant"], SCHEMA_VARIANT)
        self.assertEqual(record["bids"], ((Decimal("12.125"), Decimal("0.5")),))
        self.assertEqual(record["asks"], ((Decimal("12.25"), Decimal("4.0")),))

    def test_correct_asks_are_preserved(self):
        record = next(self.adapter().stream_records())
        self.assertEqual(record["asks"], ((Decimal("100.2"), Decimal("3.0")),))

    def test_zero_quantity_on_asks_is_preserved(self):
        record = next(self.adapter(REPLAY_1000_EQUIVALENT).stream_records())
        self.assertEqual(record["asks"][0][1], Decimal(0))
        self.assertEqual(record["ask_update_count"], 1)

    def test_negative_quantity_fails(self):
        self.assert_bad(line(dict(EVENT, asks=[{"price": 100, "quantity": -1}])))

    def test_zero_price_fails(self):
        self.assert_bad(line(dict(EVENT, bids=[{"price": 0, "quantity": 1}])))

    def test_negative_price_fails(self):
        self.assert_bad(line(dict(EVENT, asks=[{"price": -100, "quantity": 1}])))

    def test_unparseable_price_fails(self):
        self.assert_bad(line(dict(EVENT, bids=[{"price": "unparseable", "quantity": 1}])))

    def test_unparseable_quantity_fails(self):
        self.assert_bad(line(dict(EVENT, asks=[{"price": 100, "quantity": "unparseable"}])))

    def test_update_object_length_missing_or_extra_fields_fails(self):
        for update in ({}, {"price": 100}, {"quantity": 1},
                       {"price": 100, "quantity": 1, "extra": 0}):
            with self.subTest(update=update):
                self.assert_bad(line(dict(EVENT, bids=[update])))

    def test_update_type_and_legacy_pair_variant_are_rejected(self):
        for update in (None, True, 100, "price_quantity", [100, 1], ["100", "1"]):
            with self.subTest(update=update):
                self.assert_bad(line(dict(EVENT, asks=[update])))

    def test_bids_non_list_fails(self):
        for value in (None, 1, "bids", {"price": 100, "quantity": 1}):
            with self.subTest(value=value):
                self.assert_bad(line(dict(EVENT, bids=value)))

    def test_asks_non_list_fails(self):
        for value in (None, 1, "asks", {"price": 100, "quantity": 1}):
            with self.subTest(value=value):
                self.assert_bad(line(dict(EVENT, asks=value)))

    def test_numeric_strings_are_not_an_unproven_variant(self):
        for field in ("price", "quantity"):
            update = {"price": 100, "quantity": 1, field: "100.0001"}
            with self.subTest(field=field):
                self.assert_bad(line(dict(EVENT, bids=[update])))

    def test_number_boolean_null_and_object_are_rejected(self):
        for field in ("price", "quantity"):
            for value in (True, False, None, {}, []):
                update = {"price": 100, "quantity": 1, field: value}
                with self.subTest(field=field, value=value):
                    self.assert_bad(line(dict(EVENT, asks=[update])))

    def test_numeric_literal_precision_has_no_binary_float_conversion(self):
        price = "123.123456789012345678901234567890"
        quantity = "0.00000000000000000000001234567890"
        payload = ('{"eventTime":1000,"firstUpdateId":1,"finalUpdateId":2,'
                   '"bids":[{"price":' + price + ',"quantity":' + quantity + '}],"asks":[]}\n')
        record = next(self.adapter(payload).stream_records())
        self.assertEqual(record["bids"][0][0].as_tuple(), Decimal(price).as_tuple())
        self.assertEqual(record["bids"][0][1].as_tuple(), Decimal(quantity).as_tuple())

    def test_scientific_numeric_tokens_are_exact_decimals(self):
        payload = REPLAY_1000_EQUIVALENT.replace("7.25", "1.234567890123456789e-8").replace("2.0", "0e-4")
        record = next(self.adapter(payload).stream_records())
        self.assertEqual(record["bids"][0][0], Decimal("1.234567890123456789e-8"))
        self.assertEqual(record["bids"][0][1].as_tuple(), Decimal("0e-4").as_tuple())

    def test_excessive_decimal_exponent_reports_format_error(self):
        for number in ("1e-101", "1e99999999999999999999999999999999"):
            with self.subTest(number=number):
                self.assert_bad(REPLAY_1000_EQUIVALENT.replace("7.25", number))

    def test_error_has_side_update_index_and_safe_original_value(self):
        event = dict(EVENT, asks=[{"price": 100, "quantity": 1},
                                 {"price": 101, "quantity": -2}])
        error = self.assert_bad(line() + line(event), record=2)
        self.assertEqual(error.side, "asks")
        self.assertEqual(error.update_index, 1)
        self.assertIn("side=asks; update_index=1", str(error))
        self.assertIn("-2", error.safe_summary)

    def test_unlocatable_json_error_marks_context_unavailable(self):
        error = self.assert_bad("{bad\n")
        self.assertEqual(error.side, "NOT_AVAILABLE")
        self.assertEqual(error.update_index, "NOT_AVAILABLE")

    def test_safe_summary_is_bounded_and_control_characters_escaped(self):
        value = "bad\n\r\t\x1b" + "a" * 10000
        error = self.assert_bad(line(dict(EVENT, asks=[{"price": 100, "quantity": value}])))
        self.assertNotIn("\n", str(error))
        self.assertNotIn("\r", str(error))
        self.assertNotIn("\x1b", str(error))
        self.assertIn("\\n", error.safe_summary)
        self.assertLess(len(str(error)), 800)

    def test_duplicate_key_error_does_not_dump_untrusted_key(self):
        key = "untrusted" + "x" * 20000
        payload = '{"' + key + '":1,"' + key + '":2}\n'
        error = self.assert_bad(payload)
        self.assertLess(len(str(error)), 800)

    def test_unexpected_top_level_field_is_rejected(self):
        self.assert_bad(line(dict(EVENT, guessed_variant="not_supported")))

    def test_duplicate_update_fields_are_rejected(self):
        self.assert_bad(REPLAY_1000_EQUIVALENT.replace('"price":7.25', '"price":7.25,"price":7.26'))

    def test_stream_only_reads_one_bounded_line_before_first_yield(self):
        adapter = self.adapter(line() * 3)
        original = adapter._open_binary
        read_sizes = []

        class ReadlineOnly:
            def __init__(self, wrapped):
                self.wrapped = wrapped

            def read(self, *args):
                raise AssertionError("record parser must not read the entire file")

            def readline(self, size):
                read_sizes.append(size)
                return self.wrapped.readline(size)

        @contextmanager
        def guarded():
            with original() as handle:
                yield ReadlineOnly(handle)

        with mock.patch.object(adapter, "_open_binary", guarded):
            records = adapter.stream_records()
            self.assertEqual(next(records)["record_index"], 1)
            self.assertEqual(read_sizes, [MAX_LINE_BYTES + 1])
            records.close()

    def test_invalid_utf8_reports_safe_location(self):
        self.assert_bad(b"\xff\n")


if __name__ == "__main__":
    unittest.main()

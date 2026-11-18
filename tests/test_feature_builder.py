"""Source-bound builder tests with synthetic snapshots and events only."""

from decimal import Decimal as D
import unittest
from data_pipeline.features.builder import FeatureBuilder
from data_pipeline.features.schema import fields, VIEWS
from data_pipeline.orderbook.rebuilder import OrderBookRebuilder
from data_pipeline.orderbook.types import Event, Snapshot


def csv_record():
    return {"source_id": "csv", "session_id": "session", "record_index": 1,
            "event_time_ms": 10, "update_id": 123,
            "best_bid": D(99), "best_ask": D(101), "bid_volume_5": D(15),
            "ask_volume_5": D(30), "mid_price": D(999), "spread": D(999),
            "obi_5": D(1), "local_timestamp_us": 123456}


def replay_book(level_count=5):
    book = OrderBookRebuilder("session", "snapshot", "events")
    book.load_snapshot(Snapshot("snapshot", "session", 10,
        tuple((D(99-i), D(i+1)) for i in range(level_count)),
        tuple((D(101+i), D(2*(i+1))) for i in range(level_count))))
    return book


def event(index=1, first=11, final=11, bids=(), asks=()):
    return Event("events", "session", index, 100+index, first, final, bids, asks)


class FeatureBuilderTests(unittest.TestCase):
    def test_csv_aggregate_recomputes(self):
        row = FeatureBuilder("csv", "session", "csv").from_csv(csv_record())
        self.assertTrue(row["valid_feature_row"])
        self.assertEqual(row["mid_price"], D(100))
        self.assertEqual(row["spread"], D(2))
        self.assertNotEqual(row["obi_5"], D(1))

    def test_csv_fixed_columns(self):
        row = FeatureBuilder("csv", "session", "csv").from_csv(csv_record())
        self.assertEqual(tuple(row), fields(VIEWS[0]))

    def test_csv_local_timestamp_excluded(self):
        row = FeatureBuilder("csv", "session", "csv").from_csv(csv_record())
        self.assertNotIn("local_timestamp_us", row)

    def test_csv_no_labels_targets(self):
        record = csv_record()
        record.update(target=D(1), future_return=D(1), label=1)
        row = FeatureBuilder("csv", "session", "csv").from_csv(record)
        self.assertTrue(all(name not in row for name in ("target", "future_return", "label")))

    def test_csv_missing_numeric_field_retained_invalid(self):
        record = csv_record()
        del record["best_bid"]
        row = FeatureBuilder("csv", "session", "csv").from_csv(record)
        self.assertFalse(row["valid_feature_row"])
        self.assertIn("MISSING_FIELD", row["invalid_reason"])
        self.assertIsNone(row["best_bid"])
        self.assertEqual(row["record_index"], 1)

    def test_csv_missing_metadata_retained_invalid(self):
        record = csv_record()
        del record["event_time_ms"]
        row = FeatureBuilder("csv", "session", "csv").from_csv(record)
        self.assertFalse(row["valid_feature_row"])
        self.assertIsNone(row["event_time_ms"])

    def test_csv_optional_update_id_null(self):
        record = csv_record()
        del record["update_id"]
        row = FeatureBuilder("csv", "session", "csv").from_csv(record)
        self.assertTrue(row["valid_feature_row"])
        self.assertTrue(all(row[name] is None for name in ("first_update_id", "final_update_id", "local_update_id")))

    def test_csv_update_id_only_direct_alias(self):
        row = FeatureBuilder("csv", "session", "csv").from_csv(csv_record())
        self.assertEqual(row["local_update_id"], 123)
        self.assertIsNone(row["first_update_id"])
        self.assertIsNone(row["final_update_id"])

    def test_csv_bad_update_id_invalid(self):
        record = csv_record()
        record["update_id"] = True
        row = FeatureBuilder("csv", "session", "csv").from_csv(record)
        self.assertFalse(row["valid_feature_row"])
        self.assertIsNone(row["local_update_id"])

    def test_csv_cross_session_rejected(self):
        with self.assertRaisesRegex(ValueError, "SESSION_MISMATCH"):
            FeatureBuilder("csv", "another", "csv").from_csv(csv_record())

    def test_csv_cross_source_rejected(self):
        with self.assertRaisesRegex(ValueError, "SOURCE_MISMATCH"):
            FeatureBuilder("another", "session", "csv").from_csv(csv_record())

    def test_csv_cannot_create_depth(self):
        with self.assertRaisesRegex(ValueError, "CSV_DEPTH_NOT_AVAILABLE"):
            FeatureBuilder("csv", "session", "csv").from_book(replay_book(), event())

    def test_snapshot_initial_state_rejected(self):
        with self.assertRaisesRegex(ValueError, "EVENT_NOT_APPLIED"):
            FeatureBuilder("events", "session", "replay").from_book(replay_book(), event())

    def test_after_apply_creates_both_views(self):
        book, ev = replay_book(), event()
        self.assertEqual(book.apply_event(ev)["action"], "APPLY")
        rows = FeatureBuilder("events", "session", "replay").from_book(book, ev)
        self.assertEqual(tuple(rows), VIEWS)
        for view, row in rows.items():
            self.assertEqual(tuple(row), fields(view))
            self.assertTrue(row["valid_feature_row"])
            self.assertEqual(row["first_update_id"], 11)
            self.assertEqual(row["final_update_id"], 11)
            self.assertEqual(row["local_update_id"], 11)
            self.assertEqual(row["event_time_ms"], 101)

    def test_current_update_visible(self):
        book = replay_book()
        ev = event(bids=((D(99), D(5)),))
        book.apply_event(ev)
        rows = FeatureBuilder("events", "session", "replay").from_book(book, ev)
        self.assertEqual(rows[VIEWS[1]]["bid_quantity_1"], D(5))
        self.assertEqual(rows[VIEWS[0]]["bid_volume_5"], D(19))

    def test_future_event_cannot_generate_row(self):
        book = replay_book()
        book.apply_event(event())
        with self.assertRaisesRegex(ValueError, "EVENT_NOT_APPLIED"):
            FeatureBuilder("events", "session", "replay").from_book(book, event(2, 12, 12))

    def test_repeated_state_cannot_generate_duplicate(self):
        book, ev = replay_book(), event()
        book.apply_event(ev)
        builder = FeatureBuilder("events", "session", "replay")
        builder.from_book(book, ev)
        with self.assertRaisesRegex(ValueError, "EVENT_NOT_APPLIED"):
            builder.from_book(book, ev)

    def test_previous_row_not_mutated_by_future_event(self):
        book, ev = replay_book(), event()
        book.apply_event(ev)
        builder = FeatureBuilder("events", "session", "replay")
        previous = builder.from_book(book, ev)
        following = event(2, 12, 12, ((D(99), D(10)),))
        book.apply_event(following)
        new = builder.from_book(book, following)
        self.assertEqual(previous[VIEWS[1]]["bid_quantity_1"], D(1))
        self.assertEqual(new[VIEWS[1]]["bid_quantity_1"], D(10))

    def test_replay_insufficient_depth_retained(self):
        book, ev = replay_book(3), event()
        book.apply_event(ev)
        rows = FeatureBuilder("events", "session", "replay").from_book(book, ev)
        for row in rows.values():
            self.assertFalse(row["valid_feature_row"])
            self.assertIn("INSUFFICIENT_TOP5_DEPTH", row["invalid_reason"])
        self.assertIsNone(rows[VIEWS[0]]["bid_volume_5"])
        self.assertIsNone(rows[VIEWS[1]]["bid_price_5"])

    def test_replay_cross_session_rejected(self):
        book, ev = replay_book(), event()
        book.apply_event(ev)
        with self.assertRaisesRegex(ValueError, "SESSION_MISMATCH"):
            FeatureBuilder("events", "another", "replay").from_book(book, ev)

    def test_replay_cross_source_rejected(self):
        book, ev = replay_book(), event()
        book.apply_event(ev)
        with self.assertRaisesRegex(ValueError, "SOURCE_MISMATCH"):
            FeatureBuilder("another", "session", "replay").from_book(book, ev)

    def test_different_book_instance_rejected(self):
        book, ev = replay_book(), event()
        book.apply_event(ev)
        builder = FeatureBuilder("events", "session", "replay")
        builder.from_book(book, ev)
        another, following = replay_book(), event(2, 11, 12)
        another.apply_event(following)
        with self.assertRaisesRegex(ValueError, "BOOK_INSTANCE_MISMATCH"):
            builder.from_book(another, following)

    def test_replay_builder_rejects_csv(self):
        with self.assertRaisesRegex(ValueError, "CSV_SOURCE_REQUIRED"):
            FeatureBuilder("events", "session", "replay").from_csv(csv_record())

    def test_invalid_identity_rejected(self):
        with self.assertRaisesRegex(ValueError, "INVALID_IDENTITY"):
            FeatureBuilder("", "session", "csv")

    def test_unknown_source_kind_rejected(self):
        with self.assertRaisesRegex(ValueError, "INVALID_SOURCE_KIND"):
            FeatureBuilder("csv", "session", "snapshot")

    def test_csv_original_record_unchanged(self):
        record = csv_record()
        before = dict(record)
        FeatureBuilder("csv", "session", "csv").from_csv(record)
        self.assertEqual(record, before)


if __name__ == "__main__":
    unittest.main()

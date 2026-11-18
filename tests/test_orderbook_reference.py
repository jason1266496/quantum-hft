"""Independent reference tests with entirely invented snapshots and events."""

from dataclasses import replace
from decimal import Decimal, localcontext
import json
import unittest
from unittest.mock import patch

from data_pipeline.orderbook.reference import ReferenceOrderBookRebuilder
from data_pipeline.orderbook.types import BookError, Event, Snapshot


D = Decimal


def levels(*pairs):
    return tuple((D(price), D(quantity)) for price, quantity in pairs)


class ReferenceTests(unittest.TestCase):
    def snapshot(self, **changes):
        return replace(Snapshot("snapshot", "session", 10,
                                levels(("9", "2"), ("8", "3")),
                                levels(("11", "4"), ("12", "5"))), **changes)

    def event(self, **changes):
        return replace(Event("replay", "session", 1, 1000, 11, 12,
                             levels(("9.5", "6")), levels(("10.5", "7"))), **changes)

    def book(self):
        book = ReferenceOrderBookRebuilder("session", "snapshot", "replay")
        book.load_snapshot(self.snapshot())
        return book

    def assert_code(self, code, function, *args):
        with self.assertRaises(BookError) as error:
            function(*args)
        self.assertEqual(error.exception.code, code)

    def test_snapshot_initialization(self):
        book = self.book()
        self.assertEqual(book.local_update_id, 10)
        self.assertEqual(book.full_state()["bids"], {D("9"): D("2"), D("8"): D("3")})

    def test_bids_descending_asks_ascending(self):
        book = self.book()
        self.assertEqual(book.top_bids(5), list(levels(("9", "2"), ("8", "3"))))
        self.assertEqual(book.top_asks(5), list(levels(("11", "4"), ("12", "5"))))

    def test_add_new_levels(self):
        book = self.book()
        book.apply_event(self.event())
        self.assertEqual((book.best_bid(), book.best_ask()), (D("9.5"), D("10.5")))

    def test_replace_existing_quantity(self):
        book = self.book()
        book.apply_event(self.event(bids=levels(("9", "99")), asks=()))
        self.assertEqual(book.full_state()["bids"][D("9")], D("99"))
        self.assertEqual(len(book.full_state()["bids"]), 2)

    def test_delete_existing_level(self):
        book = self.book()
        book.apply_event(self.event(bids=levels(("9", "0")), asks=levels(("11", "0"))))
        self.assertEqual((book.best_bid(), book.best_ask()), (D("8"), D("12")))

    def test_delete_missing_level_noop(self):
        book = self.book()
        book.apply_event(self.event(bids=levels(("7", "0")), asks=()))
        self.assertEqual(len(book.full_state()["bids"]), 2)

    def test_snapshot_zero_quantity_omitted(self):
        book = ReferenceOrderBookRebuilder("session", "snapshot", "replay")
        book.load_snapshot(self.snapshot(bids=levels(("9", "2"), ("9", "0"), ("8", "3"))))
        self.assertEqual(book.full_state()["bids"], {D("8"): D("3")})

    def test_negative_quantity_rejected(self):
        self.assert_code("INVALID_QUANTITY", self.book().apply_event, self.event(bids=levels(("9", "-1"))))

    def test_zero_price_rejected(self):
        self.assert_code("INVALID_PRICE", self.book().apply_event, self.event(bids=levels(("0", "1"))))

    def test_negative_price_rejected(self):
        self.assert_code("INVALID_PRICE", self.book().apply_event, self.event(asks=levels(("-1", "1"))))

    def test_nonfinite_values_rejected(self):
        for price, qty, code in (("NaN", "1", "INVALID_PRICE"), ("Infinity", "1", "INVALID_PRICE"), ("9", "NaN", "INVALID_QUANTITY")):
            self.assert_code(code, self.book().apply_event, self.event(bids=levels((price, qty))))

    def test_float_state_rejected(self):
        self.assert_code("INVALID_PRICE", self.book().apply_event, self.event(bids=((9.0, D("1")),)))
        self.assert_code("INVALID_QUANTITY", self.book().apply_event, self.event(bids=((D("9"), 1.0),)))

    def test_event_failure_is_atomic_across_both_sides(self):
        book = self.book()
        before = book.full_state()
        self.assert_code("INVALID_QUANTITY", book.apply_event,
                         self.event(bids=levels(("9.5", "8")), asks=levels(("11", "-1"))))
        self.assertEqual(book.full_state(), before)
        self.assertEqual(book.applied_event_count, 0)

    def test_snapshot_failure_is_atomic(self):
        book = ReferenceOrderBookRebuilder("session", "snapshot", "replay")
        self.assert_code("INVALID_PRICE", book.load_snapshot, self.snapshot(asks=levels(("0", "1"))))
        self.assertIsNone(book.local_update_id)
        book.load_snapshot(self.snapshot())
        self.assertEqual(book.local_update_id, 10)

    def test_stale_before_snapshot_skipped(self):
        book = self.book()
        result = book.apply_event(self.event(first_update_id=8, final_update_id=10))
        self.assertEqual((result["classification"], result["action"]), ("STALE_BEFORE_SNAPSHOT", "SKIP"))
        self.assertEqual((book.local_update_id, book.skipped_event_count), (10, 1))

    def test_first_bridge_contiguous(self):
        book = self.book()
        result = book.apply_event(self.event())
        self.assertEqual(result, {"record_index": 1, "event_time": 1000, "U": 11, "u": 12,
                                  "previous_local_update_id": 10, "classification": "CONTIGUOUS", "action": "APPLY"})

    def test_first_bridge_overlapping(self):
        book = self.book()
        result = book.apply_event(self.event(first_update_id=9))
        self.assertEqual(result["classification"], "OVERLAPPING_CONTIGUOUS")
        self.assertEqual(book.local_update_id, 12)

    def test_first_bridge_failure_stops(self):
        book = self.book()
        result = book.apply_event(self.event(first_update_id=12))
        self.assertEqual((result["classification"], result["action"]), ("FIRST_EVENT_BRIDGE_FAILURE", "STOP"))
        self.assertEqual(book.continuity_error_count, 1)
        self.assertEqual(book.local_update_id, 10)
        self.assert_code("TERMINAL_STATE", book.apply_event, self.event())

    def test_subsequent_contiguous(self):
        book = self.book()
        book.apply_event(self.event())
        result = book.apply_event(self.event(first_update_id=13, final_update_id=15))
        self.assertEqual(result["classification"], "CONTIGUOUS")
        self.assertEqual(book.local_update_id, 15)

    def test_subsequent_overlapping(self):
        book = self.book()
        book.apply_event(self.event())
        result = book.apply_event(self.event(first_update_id=11, final_update_id=15))
        self.assertEqual(result["classification"], "OVERLAPPING_CONTIGUOUS")
        self.assertEqual(book.local_update_id, 15)

    def test_duplicate_after_bridge_skipped(self):
        book = self.book()
        event = self.event()
        book.apply_event(event)
        before = book.full_state()
        result = book.apply_event(event)
        self.assertEqual(result["classification"], "STALE_OR_DUPLICATE")
        self.assertEqual(book.full_state(), before)

    def test_gap_is_terminal_and_does_not_apply(self):
        book = self.book()
        book.apply_event(self.event())
        before = book.full_state()
        result = book.apply_event(self.event(first_update_id=14, final_update_id=15))
        self.assertEqual((result["classification"], result["action"]), ("UPDATE_ID_GAP", "STOP"))
        self.assertEqual(book.full_state(), before)
        self.assert_code("TERMINAL_STATE", book.apply_event, self.event(first_update_id=13, final_update_id=15))

    def test_crossed_book_recorded(self):
        book = self.book()
        book.apply_event(self.event(bids=levels(("11", "1")), asks=()))
        self.assertTrue(book.state_summary()["crossed"])
        self.assertEqual(book.crossed_book_count, 1)

    def test_quality_checked_after_complete_event(self):
        book = self.book()
        book.apply_event(self.event(bids=levels(("11.5", "1")), asks=levels(("11", "0"))))
        self.assertFalse(book.state_summary()["crossed"])
        self.assertEqual(book.crossed_book_count, 0)

    def test_empty_bid_side_recorded(self):
        book = self.book()
        book.apply_event(self.event(bids=levels(("9", "0"), ("8", "0")), asks=()))
        self.assertIsNone(book.best_bid())
        self.assertTrue(book.state_summary()["empty"])
        self.assertEqual(book.empty_side_count, 1)

    def test_empty_ask_side_recorded(self):
        book = self.book()
        book.apply_event(self.event(bids=(), asks=levels(("11", "0"), ("12", "0"))))
        self.assertIsNone(book.best_ask())
        self.assertEqual(book.empty_side_count, 1)

    def test_skipped_events_do_not_recount_quality(self):
        book = self.book()
        event = self.event(bids=levels(("11", "1")), asks=())
        book.apply_event(event)
        book.apply_event(event)
        self.assertEqual(book.crossed_book_count, 1)

    def test_top_five_correct(self):
        book = self.book()
        book.apply_event(self.event(bids=levels(*((str(x), "1") for x in range(1, 8))), asks=levels(*((str(x), "1") for x in range(13, 21)))))
        self.assertEqual([p for p, q in book.top_bids(5)], list(map(D, ("9", "8", "7", "6", "5"))))
        self.assertEqual([p for p, q in book.top_asks(5)], list(map(D, ("11", "12", "13", "14", "15"))))

    def test_decimal_precision_preserved_under_low_context(self):
        book = self.book()
        price, qty = "9.12345678901234567890123456789", "12345678901234567890.123456789"
        with localcontext() as context:
            context.prec = 2
            book.apply_event(self.event(bids=levels((price, qty)), asks=()))
        self.assertEqual(book.full_state()["bids"][D(price)], D(qty))

    def test_full_state_returns_independent_copies(self):
        book = self.book()
        state = book.full_state()
        state["bids"].clear()
        state["asks"][D("1")] = D("9")
        self.assertEqual((book.best_bid(), book.best_ask()), (D("9"), D("11")))

    def test_state_summary_is_json_safe(self):
        result = self.book().state_summary()
        self.assertEqual(json.loads(json.dumps(result)), result)
        self.assertEqual(result["best_bid"], "9")
        self.assertEqual(result["top_bids"], [["9", "2"], ["8", "3"]])

    def test_hash_is_deterministic(self):
        a, b = self.book(), self.book()
        a.apply_event(self.event())
        b.apply_event(self.event())
        self.assertEqual(a.canonical_state_hash(), b.canonical_state_hash())

    def test_cross_session_snapshot_rejected(self):
        book = ReferenceOrderBookRebuilder("session", "snapshot", "replay")
        self.assert_code("SESSION_MISMATCH", book.load_snapshot, self.snapshot(session_id="other"))

    def test_cross_session_event_rejected(self):
        self.assert_code("SESSION_MISMATCH", self.book().apply_event, self.event(session_id="other"))

    def test_wrong_snapshot_source_rejected(self):
        book = ReferenceOrderBookRebuilder("session", "snapshot", "replay")
        self.assert_code("SOURCE_MISMATCH", book.load_snapshot, self.snapshot(source_id="other"))

    def test_wrong_replay_source_rejected(self):
        self.assert_code("SOURCE_MISMATCH", self.book().apply_event, self.event(source_id="other"))

    def test_snapshot_reloading_rejected(self):
        self.assert_code("SNAPSHOT_ALREADY_LOADED", self.book().load_snapshot, self.snapshot())

    def test_no_snapshot_apply_rejected(self):
        book = ReferenceOrderBookRebuilder("session", "snapshot", "replay")
        self.assert_code("SNAPSHOT_REQUIRED", book.apply_event, self.event())

    def test_invalid_depth_rejected(self):
        for depth in (-1, 1.5, True):
            self.assert_code("INVALID_DEPTH", self.book().top_bids, depth)
            self.assert_code("INVALID_DEPTH", self.book().top_asks, depth)
        self.assertEqual(self.book().top_bids(0), [])

    def test_invalid_event_metadata_rejected(self):
        for changes, code in (({"first_update_id": 13, "final_update_id": 12}, "INVALID_UPDATE_ID"),
                              ({"first_update_id": True}, "INVALID_UPDATE_ID"),
                              ({"record_index": 0}, "INVALID_RECORD_INDEX"),
                              ({"event_time": -1}, "INVALID_EVENT_TIME")):
            self.assert_code(code, self.book().apply_event, self.event(**changes))

    def test_reference_does_not_call_main_apply(self):
        from data_pipeline.orderbook.rebuilder import OrderBookRebuilder
        with patch.object(OrderBookRebuilder, "apply_event", side_effect=AssertionError("main apply called")):
            book = self.book()
            self.assertEqual(book.apply_event(self.event())["action"], "APPLY")

    def test_reference_matches_main_through_mixed_updates(self):
        from data_pipeline.orderbook.rebuilder import OrderBookRebuilder
        primary = OrderBookRebuilder("session", "snapshot", "replay")
        primary.load_snapshot(self.snapshot())
        reference = self.book()
        events = (self.event(first_update_id=8, final_update_id=10), self.event(),
                  self.event(first_update_id=12, final_update_id=14, bids=levels(("9.5", "0"), ("8.75", "2"))),
                  self.event(first_update_id=12, final_update_id=14),
                  self.event(first_update_id=15, final_update_id=16, bids=(), asks=levels(("10.5", "0"))))
        for event in events:
            self.assertEqual(primary.apply_event(event), reference.apply_event(event))
            self.assertEqual(primary.full_state(), reference.full_state())
            self.assertEqual(primary.state_summary(), reference.state_summary())
            self.assertEqual(primary.canonical_state_hash(), reference.canonical_state_hash())


if __name__ == "__main__":
    unittest.main()

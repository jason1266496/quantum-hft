"""Synthetic Decimal books exercise application, isolation, and lazy heaps."""

from dataclasses import FrozenInstanceError, replace
from decimal import Decimal, localcontext
import json
import unittest

from data_pipeline.orderbook.rebuilder import OrderBookRebuilder
from data_pipeline.orderbook.types import BookError, Event, Snapshot


D = Decimal


def levels(*pairs):
    return tuple((D(price), D(quantity)) for price, quantity in pairs)


def snapshot(**changes):
    return replace(Snapshot("snapshot", "session", 100,
                            levels(("99", "2"), ("98", "3")),
                            levels(("101", "4"), ("102", "5"))), **changes)


def event(U=101, u=101, **changes):
    return replace(Event("replay", "session", 1, 1700000000000, U, u, (), ()), **changes)


def book(initial=None):
    result = OrderBookRebuilder("session", "snapshot", "replay")
    result.load_snapshot(snapshot() if initial is None else initial)
    return result


class RebuilderTests(unittest.TestCase):
    def assert_code(self, code, callable_, *args):
        with self.assertRaises(BookError) as caught:
            callable_(*args)
        self.assertEqual(caught.exception.code, code)

    def test_snapshot_initialization(self):
        b = book()
        self.assertEqual(b.local_update_id, 100)
        self.assertEqual(b.full_state()["bids"], {D("99"): D("2"), D("98"): D("3")})
        self.assertEqual(b.applied_event_count, 0)

    def test_bid_sort_descending(self):
        self.assertEqual(book().top_bids(9), list(levels(("99", "2"), ("98", "3"))))

    def test_ask_sort_ascending(self):
        self.assertEqual(book().top_asks(9), list(levels(("101", "4"), ("102", "5"))))

    def test_add_level(self):
        b = book()
        b.apply_event(event(bids=levels(("100", "6"))))
        self.assertEqual(b.best_bid(), D("100"))
        self.assertEqual(b.full_state()["bids"][D("100")], D("6"))

    def test_overwrite_level_does_not_duplicate_heap(self):
        b = book()
        b.apply_event(event(bids=levels(("99", "8"))))
        self.assertEqual(b.top_bids(1), [(D("99"), D("8"))])
        self.assertEqual(len(b._bid_heap), 2)

    def test_delete_existing_best_bid(self):
        b = book()
        b.apply_event(event(bids=levels(("99", "0"))))
        self.assertEqual(b.best_bid(), D("98"))

    def test_delete_existing_best_ask(self):
        b = book()
        b.apply_event(event(asks=levels(("101", "0"))))
        self.assertEqual(b.best_ask(), D("102"))

    def test_delete_missing_price_no_effect(self):
        b = book()
        old = b.full_state()
        b.apply_event(event(bids=levels(("1", "0")), asks=levels(("200", "0"))))
        self.assertEqual(b.full_state()["bids"], old["bids"])
        self.assertEqual(b.full_state()["asks"], old["asks"])

    def test_negative_quantity_atomic_failure(self):
        b = book()
        before = b.full_state()
        self.assert_code("INVALID_QUANTITY", b.apply_event,
                         event(bids=levels(("100", "5")), asks=levels(("103", "-1"))))
        self.assertEqual(b.full_state(), before)
        self.assertEqual(b.applied_event_count, 0)

    def test_zero_price_failure(self):
        self.assert_code("INVALID_PRICE", book().apply_event, event(bids=levels(("0", "1"))))

    def test_negative_price_failure(self):
        self.assert_code("INVALID_PRICE", book().apply_event, event(asks=levels(("-1", "1"))))

    def test_nonfinite_prices_and_quantities_fail(self):
        for value in ("NaN", "sNaN", "Infinity", "-Infinity"):
            for side, code in ((0, "INVALID_PRICE"), (1, "INVALID_QUANTITY")):
                level = [D("99"), D("1")]
                level[side] = D(value)
                with self.subTest(value=value, field=side):
                    self.assert_code(code, book().apply_event, event(bids=(tuple(level),)))

    def test_float_int_and_bool_are_not_book_numbers(self):
        for value in (1.0, 1, True, "1"):
            with self.subTest(value=value):
                self.assert_code("INVALID_PRICE", book().apply_event, event(bids=((value, D("1")),)))
                self.assert_code("INVALID_QUANTITY", book().apply_event, event(asks=((D("103"), value),)))

    def test_initial_stale_event_skips_without_mutation(self):
        b = book()
        before = b.full_state()
        result = b.apply_event(event(98, 100, bids=levels(("99", "0"))))
        self.assertEqual(result["classification"], "STALE_BEFORE_SNAPSHOT")
        self.assertEqual(result["action"], "SKIP")
        self.assertEqual(b.full_state(), before)
        self.assertEqual(b.skipped_event_count, 1)
        self.assertEqual(b.continuity_error_count, 0)

    def test_bridge_after_stale_is_still_first_bridge(self):
        b = book()
        b.apply_event(event(99, 100))
        self.assertEqual(b.apply_event(event(101, 105))["action"], "APPLY")
        self.assertEqual(b.local_update_id, 105)

    def test_first_bridge_failure_stops_and_preserves_state(self):
        b = book()
        before = b.full_state()
        result = b.apply_event(event(102, 104, bids=levels(("99", "0"))))
        self.assertEqual(result["classification"], "FIRST_EVENT_BRIDGE_FAILURE")
        self.assertEqual(result["action"], "STOP")
        self.assertEqual(b.full_state(), before)
        self.assertEqual(b.continuity_error_count, 1)
        self.assert_code("TERMINAL_STATE", b.apply_event, event())

    def test_contiguous_event(self):
        b = book()
        b.apply_event(event(101, 103))
        result = b.apply_event(event(104, 106))
        self.assertEqual(result["classification"], "CONTIGUOUS")
        self.assertEqual(result["previous_local_update_id"], 103)
        self.assertEqual(b.local_update_id, 106)

    def test_overlapping_event(self):
        b = book()
        b.apply_event(event(101, 103))
        result = b.apply_event(event(102, 105))
        self.assertEqual(result["classification"], "OVERLAPPING_CONTIGUOUS")
        self.assertEqual(b.applied_event_count, 2)

    def test_duplicate_event_skipped(self):
        b = book()
        b.apply_event(event(101, 103))
        before = b.full_state()
        result = b.apply_event(event(101, 103, asks=levels(("101", "0"))))
        self.assertEqual(result["classification"], "STALE_OR_DUPLICATE")
        self.assertEqual(b.full_state(), before)

    def test_gap_stops_and_cannot_resume(self):
        b = book()
        b.apply_event(event())
        before = b.full_state()
        result = b.apply_event(event(103, 104, bids=levels(("100", "1"))))
        self.assertEqual(result["classification"], "UPDATE_ID_GAP")
        self.assertEqual(b.full_state(), before)
        self.assert_code("TERMINAL_STATE", b.apply_event, event(102, 102))

    def test_crossed_book_is_recorded(self):
        b = book()
        b.apply_event(event(bids=levels(("101", "1"))))
        self.assertTrue(b.state_summary()["crossed"])
        self.assertEqual(b.crossed_book_count, 1)

    def test_crossing_checked_only_after_complete_event(self):
        b = book()
        b.apply_event(event(bids=levels(("102", "1")), asks=levels(("101", "0"), ("102", "0"), ("103", "1"))))
        self.assertFalse(b.state_summary()["crossed"])
        self.assertEqual(b.crossed_book_count, 0)
        self.assertEqual(b.empty_side_count, 0)

    def test_empty_bid_side(self):
        b = book()
        b.apply_event(event(bids=levels(("99", "0"), ("98", "0"))))
        self.assertIsNone(b.best_bid())
        self.assertTrue(b.state_summary()["empty"])
        self.assertEqual(b.empty_side_count, 1)

    def test_empty_ask_side(self):
        b = book()
        b.apply_event(event(asks=levels(("101", "0"), ("102", "0"))))
        self.assertIsNone(b.best_ask())
        self.assertEqual(b.empty_side_count, 1)

    def test_snapshot_quality_is_checked(self):
        self.assertEqual(book(snapshot(asks=levels(("98", "1")))).crossed_book_count, 1)
        self.assertEqual(book(snapshot(bids=())).empty_side_count, 1)

    def test_snapshot_zero_levels_omitted(self):
        b = book(snapshot(bids=levels(("99", "0"), ("98", "1"))))
        self.assertEqual(b.top_bids(2), [(D("98"), D("1"))])

    def test_top_five_correct(self):
        b = book(snapshot(bids=tuple((D(i), D(i + 1)) for i in range(1, 8)),
                          asks=tuple((D(i), D(i + 1)) for i in range(20, 27))))
        self.assertEqual([p for p, q in b.top_bids(5)], list(map(D, (7, 6, 5, 4, 3))))
        self.assertEqual([p for p, q in b.top_asks(5)], list(map(D, (20, 21, 22, 23, 24))))

    def test_top_zero_and_bad_counts(self):
        b = book()
        self.assertEqual(b.top_bids(0), [])
        for n in (-1, True, 1.0, "5"):
            self.assert_code("INVALID_TOP_COUNT", b.top_asks, n)

    def test_decimal_precision_under_low_context(self):
        price = D("99.123456789012345678901234567890123456789")
        quantity = D("0.123456789012345678901234567890123456789")
        with localcontext() as context:
            context.prec = 3
            b = book()
            b.apply_event(event(bids=((price, quantity),)))
            self.assertEqual(b.best_bid(), price)
            self.assertEqual(b.top_bids(1), [(price, quantity)])
            self.assertEqual(b.full_state()["bids"][price], quantity)

    def test_delete_then_readd_unpruned_price(self):
        b = book()
        b.apply_event(event(bids=levels(("98", "0"))))
        b.apply_event(event(102, 102, bids=levels(("98", "8"), ("99", "0"))))
        self.assertEqual(b.best_bid(), D("98"))
        self.assertEqual(b.top_bids(1), [(D("98"), D("8"))])

    def test_delete_then_readd_pruned_best(self):
        b = book()
        b.apply_event(event(asks=levels(("101", "0"))))
        self.assertEqual(b.best_ask(), D("102"))
        b.apply_event(event(102, 102, asks=levels(("101", "9"))))
        self.assertEqual(b.best_ask(), D("101"))

    def test_duplicate_price_updates_in_same_event_are_sequential(self):
        b = book()
        b.apply_event(event(bids=levels(("99", "4"), ("99", "0"), ("99", "9"))))
        self.assertEqual(b.top_bids(1), [(D("99"), D("9"))])
        self.assertEqual(len(b._bid_heap), 2)

    def test_heap_compaction_bounds_churn(self):
        b = book()
        for offset in range(180):
            price = D("0." + str(offset + 1000))
            b.apply_event(event(101 + offset, 101 + offset,
                                bids=((price, D("1")), (price, D("0"))),
                                asks=((D(1000 + offset), D("1")), (D(1000 + offset), D("0")))))
        self.assertLessEqual(len(b._bid_heap), max(64, 2 * len(b._bids) + 32))
        self.assertLessEqual(len(b._ask_heap), max(64, 2 * len(b._asks) + 32))
        self.assertEqual(b.best_bid(), D("99"))
        self.assertEqual(b.best_ask(), D("101"))

    def test_full_state_is_an_independent_copy(self):
        b = book()
        state = b.full_state()
        state["bids"].clear()
        state["asks"][D("1")] = D("1")
        state["local_update_id"] = 0
        self.assertEqual(b.best_bid(), D("99"))
        self.assertEqual(b.best_ask(), D("101"))
        self.assertEqual(b.local_update_id, 100)

    def test_state_summary_is_json_safe(self):
        summary = book().state_summary()
        self.assertEqual(json.loads(json.dumps(summary)), summary)
        self.assertEqual(summary["top_bids"][0], ["99", "2"])

    def test_hash_is_deterministic(self):
        a, b = book(), book()
        a.apply_event(event(bids=levels(("100.0", "3.00"))))
        b.apply_event(event(bids=levels(("100", "3"))))
        self.assertEqual(a.canonical_state_hash(), b.canonical_state_hash())

    def test_session_mismatch_rejected(self):
        self.assert_code("SESSION_MISMATCH", book().apply_event, event(session_id="other"))
        fresh = OrderBookRebuilder("session", "snapshot", "replay")
        self.assert_code("SESSION_MISMATCH", fresh.load_snapshot, snapshot(session_id="other"))

    def test_source_mismatch_rejected(self):
        self.assert_code("SOURCE_MISMATCH", book().apply_event, event(source_id="other"))
        fresh = OrderBookRebuilder("session", "snapshot", "replay")
        self.assert_code("SOURCE_MISMATCH", fresh.load_snapshot, snapshot(source_id="other"))

    def test_cannot_reload_snapshot(self):
        self.assert_code("SNAPSHOT_ALREADY_LOADED", book().load_snapshot, snapshot())

    def test_must_load_snapshot_first(self):
        fresh = OrderBookRebuilder("session", "snapshot", "replay")
        self.assert_code("SNAPSHOT_REQUIRED", fresh.apply_event, event())
        self.assert_code("SNAPSHOT_REQUIRED", fresh.full_state)

    def test_invalid_snapshot_is_atomic(self):
        fresh = OrderBookRebuilder("session", "snapshot", "replay")
        self.assert_code("INVALID_QUANTITY", fresh.load_snapshot, snapshot(asks=levels(("101", "-2"))))
        fresh.load_snapshot(snapshot())
        self.assertEqual(fresh.best_ask(), D("101"))

    def test_invalid_event_metadata_rejected(self):
        for changes, code in (({"record_index": 0}, "INVALID_RECORD_INDEX"),
                              ({"record_index": True}, "INVALID_RECORD_INDEX"),
                              ({"event_time": -1}, "INVALID_EVENT_TIME"),
                              ({"first_update_id": True}, "INVALID_UPDATE_ID"),
                              ({"final_update_id": 99}, "INVALID_UPDATE_ID")):
            with self.subTest(changes=changes):
                self.assert_code(code, book().apply_event, event(**changes))

    def test_input_types_are_frozen(self):
        for value, field in ((snapshot(), "last_update_id"), (event(), "event_time")):
            with self.assertRaises(FrozenInstanceError):
                setattr(value, field, 0)
        with self.assertRaises(BookError):
            snapshot(bids=[(D("1"), D("2"))])

    def test_from_adapter_record_preserves_decimal_identity(self):
        pair = levels(("99.123456789012345678901234567890123456789", "2"))
        record = {"source_id": "replay", "session_id": "session", "record_index": 1,
                  "eventTime": 1, "firstUpdateId": 101, "finalUpdateId": 102,
                  "bids": pair, "asks": (), "schema_variant": "capture_object_price_quantity_v1"}
        output = Event.from_record(record)
        self.assertIs(output.bids, pair)
        self.assertIs(output.bids[0][0], pair[0][0])
        self.assertEqual(output.event_time, 1)

    def test_local_timestamp_is_forbidden(self):
        self.assert_code("FORBIDDEN_TIMESTAMP", Event.from_record, {"local_timestamp_us": 123})

    def test_missing_adapter_record_fields_rejected(self):
        self.assert_code("INVALID_EVENT_RECORD", Event.from_record, {})
        self.assert_code("INVALID_EVENT_RECORD", Event.from_record, [])

    def test_summary_and_reads_do_not_increment_quality_counts(self):
        b = book(snapshot(bids=()))
        for _ in range(4):
            b.state_summary()
            b.best_bid()
            b.canonical_state_hash()
        b.apply_event(event(90, 100))
        self.assertEqual(b.empty_side_count, 1)


if __name__ == "__main__":
    unittest.main()

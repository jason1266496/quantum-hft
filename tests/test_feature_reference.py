"""Artificial fixtures for the independent canonical-book feature reference."""

import ast
import copy
from decimal import Context, Decimal, Inexact, ROUND_DOWN, ROUND_HALF_EVEN, localcontext
import inspect
import unittest
from unittest.mock import patch

from data_pipeline.features.reference import reference_features
from data_pipeline.features.schema import fields
from data_pipeline.orderbook.canonical import canonical_state
from data_pipeline.orderbook.rebuilder import OrderBookRebuilder
from data_pipeline.orderbook.types import Event, Snapshot

D = Decimal
A = "aggregate_core_v1"
T = "depth_top5_v1"
CTX = Context(prec=50, rounding=ROUND_HALF_EVEN, Emin=-999999, Emax=999999)


def fixture(bid_quantities=("1", "2", "3", "4", "5"),
            ask_quantities=("5", "4", "3", "2", "1")):
    bids = [[str(99 - i), str(quantity)] for i, quantity in enumerate(bid_quantities)]
    asks = [[str(101 + i), str(quantity)] for i, quantity in enumerate(ask_quantities)]
    state = {"local_update_id": 12, "bids": bids, "asks": asks,
             "bid_level_count": len(bids), "ask_level_count": len(asks),
             "best_bid": bids[0][0] if bids else None,
             "best_ask": asks[0][0] if asks else None}
    metadata = {"source_id": "artificial_events", "session_id": "artificial_session",
                "record_index": 1, "event_time_ms": 1000,
                "first_update_id": 11, "final_update_id": 12, "local_update_id": 12}
    return state, metadata


class FeatureReferenceTests(unittest.TestCase):
    def rows(self, **kwargs):
        return reference_features(*fixture(**kwargs))

    def test_metadata_and_schema_order_are_exact(self):
        rows = self.rows()
        for view, row in rows.items():
            self.assertEqual(tuple(row), fields(view))
            self.assertEqual(row["schema_version"], "1.0")
            self.assertEqual(row["feature_view"], view)
            self.assertEqual(row["source_id"], "artificial_events")
            self.assertEqual(row["session_id"], "artificial_session")
            self.assertEqual(row["record_index"], 1)
            self.assertEqual(row["event_time_ms"], 1000)
            self.assertEqual((row["first_update_id"], row["final_update_id"],
                              row["local_update_id"]), (11, 12, 12))

    def test_mid_spread_and_basis_points(self):
        for row in self.rows().values():
            self.assertEqual(row["mid_price"], D("100"))
            self.assertEqual(row["spread"], D("2"))
            self.assertEqual(row["spread_bps"], D("200"))

    def test_aggregate_top_five_volume_and_obi(self):
        row = self.rows()[A]
        self.assertEqual(row["best_bid"], D("99"))
        self.assertEqual(row["best_ask"], D("101"))
        self.assertEqual(row["bid_volume_5"], D("15"))
        self.assertEqual(row["ask_volume_5"], D("15"))
        self.assertEqual(row["obi_5"], D("0"))

    def test_all_depth_prices_quantities_and_cumulative_sums(self):
        row = self.rows()[T]
        for index in range(1, 6):
            self.assertEqual(row[f"bid_price_{index}"], D(str(100 - index)))
            self.assertEqual(row[f"ask_price_{index}"], D(str(100 + index)))
            self.assertEqual(row[f"bid_quantity_{index}"], D(str(index)))
            self.assertEqual(row[f"ask_quantity_{index}"], D(str(6 - index)))
            self.assertEqual(row[f"cumulative_bid_quantity_{index}"],
                             D(str(sum(range(1, index + 1)))))
            self.assertEqual(row[f"cumulative_ask_quantity_{index}"],
                             D(str(sum(range(6 - index, 6)))))

    def test_all_depth_distances(self):
        row = self.rows()[T]
        for index in range(1, 6):
            self.assertEqual(row[f"bid_distance_bps_{index}"], D(str(index * 100)))
            self.assertEqual(row[f"ask_distance_bps_{index}"], D(str(index * 100)))

    def test_level_imbalance_and_obi_1_3_5(self):
        row = self.rows()[T]
        with localcontext(CTX):
            for index in range(1, 6):
                self.assertEqual(row[f"level_imbalance_{index}"],
                                 D(str(2 * index - 6)) / D("6"))
            self.assertEqual(row["obi_1"], D("-4") / D("6"))
            self.assertEqual(row["obi_3"], D("-6") / D("18"))
            self.assertEqual(row["obi_5"], D("0"))

    def test_microprice_and_deviation(self):
        row = self.rows()[T]
        with localcontext(CTX):
            expected = D("596") / D("6")
            self.assertEqual(row["microprice"], expected)
            self.assertEqual(row["microprice_deviation_bps"],
                             (expected - D("100")) / D("100") * D("10000"))
        self.assertGreaterEqual(row["microprice"], D("99"))
        self.assertLessEqual(row["microprice"], D("101"))

    def test_obi_and_imbalance_are_bounded_for_nonnegative_quantity(self):
        row = self.rows(bid_quantities=("0", "0", "0", "0", "0"))[T]
        for key in ("obi_1", "obi_3", "obi_5") + tuple(
                f"level_imbalance_{i}" for i in range(1, 6)):
            self.assertEqual(row[key], D("-1"))
        self.assertEqual(row["microprice"], D("99"))

    def test_all_feature_numbers_are_decimal(self):
        for view, row in self.rows().items():
            for name, value in row.items():
                if name not in ("schema_version", "feature_view", "source_id", "session_id",
                                "record_index", "event_time_ms", "first_update_id",
                                "final_update_id", "local_update_id",
                                "valid_feature_row", "invalid_reason"):
                    self.assertIs(type(value), Decimal, (view, name))

    def test_fifty_digit_precision_preserved(self):
        state, metadata = fixture()
        state["bids"][0][1] = "1.123456789012345678901234567890123456789"
        result = reference_features(state, metadata)[T]
        self.assertEqual(result["bid_quantity_1"],
                         D("1.123456789012345678901234567890123456789"))
        with localcontext(CTX):
            q = D(state["bids"][0][1])
            expected = (q - D("5")) / (q + D("5"))
            self.assertEqual(result["obi_1"], expected)

    def test_ambient_precision_rounding_and_traps_do_not_change_result(self):
        expected = self.rows()
        with localcontext() as ambient:
            ambient.prec = 2
            ambient.rounding = ROUND_DOWN
            ambient.traps[Inexact] = True
            actual = self.rows()
            self.assertEqual(ambient.prec, 2)
            self.assertIs(ambient.traps[Inexact], True)
        self.assertEqual(actual, expected)

    def test_full_state_and_top_five_projection_match(self):
        state, metadata = fixture()
        state["bids"].extend([["94", "100000"], ["93", "200000"]])
        state["asks"].extend([["106", "500000"], ["107", "600000"]])
        state["bid_level_count"] = state["ask_level_count"] = 7
        projection = copy.deepcopy(state)
        projection["bids"] = projection["bids"][:5]
        projection["asks"] = projection["asks"][:5]
        projection["state_scope"] = "TOP5_CANONICAL_PROJECTION"
        self.assertEqual(reference_features(state, metadata),
                         reference_features(projection, metadata))

    def test_lower_depth_cannot_change_top_five_features(self):
        state, metadata = fixture()
        expected = reference_features(state, metadata)
        state["bids"].append(["0.1", "999999999999999"])
        state["asks"].append(["999999999", "999999999999999"])
        state["bid_level_count"] += 1
        state["ask_level_count"] += 1
        self.assertEqual(reference_features(state, metadata), expected)

    def test_inputs_are_not_mutated(self):
        state, metadata = fixture()
        before = copy.deepcopy((state, metadata))
        reference_features(state, metadata)
        self.assertEqual((state, metadata), before)

    def test_separate_calls_do_not_mix_sessions(self):
        state, metadata = fixture()
        first = reference_features(state, metadata)
        other = dict(metadata, source_id="other_source", session_id="other_session",
                     record_index=50, event_time_ms=2000)
        second = reference_features(state, other)
        for view in (A, T):
            self.assertEqual(first[view]["source_id"], "artificial_events")
            self.assertEqual(second[view]["source_id"], "other_source")
            self.assertEqual(second[view]["session_id"], "other_session")
            self.assertEqual(second[view]["record_index"], 50)

    def test_future_local_timestamp_and_targets_do_not_enter_view(self):
        state, metadata = fixture()
        metadata.update(local_timestamp_us=12345, future_return="9", target="up",
                        future_events=[{"event_time_ms": 2000}])
        for row in reference_features(state, metadata).values():
            self.assertNotIn("local_timestamp_us", row)
            self.assertNotIn("future_return", row)
            self.assertNotIn("target", row)
            self.assertNotIn("future_events", row)

    def test_views_do_not_mix_depth_and_aggregate_only_columns(self):
        rows = self.rows()
        self.assertNotIn("bid_price_1", rows[A])
        self.assertNotIn("microprice", rows[A])
        self.assertNotIn("bid_volume_5", rows[T])
        self.assertNotIn("best_bid", rows[T])

    def test_crossed_book_is_retained_invalid(self):
        state, metadata = fixture()
        state["bids"][0][0] = "102"
        for row in reference_features(state, metadata).values():
            self.assertFalse(row["valid_feature_row"])
            self.assertIn("CROSSED_BOOK", row["invalid_reason"])
            self.assertEqual(row["spread"], D("-1"))

    def test_empty_side_is_retained_invalid(self):
        state, metadata = fixture(bid_quantities=())
        for row in reference_features(state, metadata).values():
            self.assertFalse(row["valid_feature_row"])
            self.assertIn("EMPTY_SIDE", row["invalid_reason"])
            self.assertIn("INSUFFICIENT_TOP5_DEPTH", row["invalid_reason"])
            self.assertIsNone(row["mid_price"])

    def test_insufficient_top_five_is_not_filled(self):
        state, metadata = fixture(bid_quantities=("1", "2"))
        rows = reference_features(state, metadata)
        self.assertIsNone(rows[A]["bid_volume_5"])
        self.assertIsNone(rows[A]["obi_5"])
        self.assertIsNone(rows[T]["bid_price_3"])
        self.assertIsNone(rows[T]["cumulative_bid_quantity_3"])
        self.assertEqual(rows[T]["cumulative_bid_quantity_2"], D("3"))
        for row in rows.values():
            self.assertFalse(row["valid_feature_row"])
            self.assertIn("INSUFFICIENT_TOP5_DEPTH", row["invalid_reason"])

    def test_zero_depth_denominator_never_becomes_zero_obi(self):
        rows = self.rows(bid_quantities=("0",) * 5, ask_quantities=("0",) * 5)
        for row in rows.values():
            self.assertFalse(row["valid_feature_row"])
            self.assertIsNone(row["obi_5"])
            self.assertIn("ZERO_DEPTH_DENOMINATOR", row["invalid_reason"])
        self.assertIsNone(rows[T]["microprice"])
        self.assertIn("ZERO_MICROPRICE_DENOMINATOR", rows[T]["invalid_reason"])

    def test_single_zero_level_keeps_null_and_warning(self):
        row = self.rows(bid_quantities=("1", "0", "3", "4", "5"),
                        ask_quantities=("5", "0", "3", "2", "1"))[T]
        self.assertIsNone(row["level_imbalance_2"])
        self.assertTrue(row["valid_feature_row"])
        self.assertEqual(row["invalid_reason"], "ZERO_LEVEL_DENOMINATOR")

    def test_negative_quantity_is_retained_invalid(self):
        rows = self.rows(bid_quantities=("-1", "2", "3", "4", "5"))
        for row in rows.values():
            self.assertFalse(row["valid_feature_row"])
            self.assertIn("INVALID_QUANTITY", row["invalid_reason"])

    def test_nonpositive_price_is_retained_invalid(self):
        state, metadata = fixture()
        state["bids"][4][0] = "0"
        for row in reference_features(state, metadata).values():
            self.assertFalse(row["valid_feature_row"])
            self.assertIn("INVALID_PRICE", row["invalid_reason"])

    def test_nonfinite_values_are_not_calculated(self):
        for text in ("NaN", "sNaN", "Infinity", "-Infinity"):
            with self.subTest(value=text):
                state, metadata = fixture()
                state["bids"][0][1] = text
                for row in reference_features(state, metadata).values():
                    self.assertFalse(row["valid_feature_row"])
                    self.assertIn("NON_FINITE_VALUE", row["invalid_reason"])

    def test_float_int_and_boolean_numeric_sources_are_rejected(self):
        for value in (1.5, 1, True, D("1.5")):
            with self.subTest(value=value):
                state, metadata = fixture()
                state["asks"][1][1] = value
                for row in reference_features(state, metadata).values():
                    self.assertFalse(row["valid_feature_row"])
                    self.assertIn("INVALID_NUMERIC_TYPE", row["invalid_reason"])

    def test_bad_decimal_string_is_retained_invalid(self):
        state, metadata = fixture()
        state["asks"][2][1] = "bad"
        for row in reference_features(state, metadata).values():
            self.assertFalse(row["valid_feature_row"])
            self.assertIn("INVALID_NUMERIC_TYPE", row["invalid_reason"])

    def test_missing_decimal_is_retained_invalid(self):
        state, metadata = fixture()
        state["bids"][0][1] = None
        for row in reference_features(state, metadata).values():
            self.assertFalse(row["valid_feature_row"])
            self.assertIn("MISSING_VALUE", row["invalid_reason"])

    def test_invalid_reasons_are_sorted_and_unique(self):
        state, metadata = fixture(bid_quantities=())
        state["asks"][0][1] = "-1"
        for row in reference_features(state, metadata).values():
            reasons = row["invalid_reason"].split(";")
            self.assertEqual(reasons, sorted(set(reasons)))

    def test_missing_replay_identity_is_rejected(self):
        for key in ("source_id", "session_id", "record_index", "event_time_ms",
                    "first_update_id", "final_update_id", "local_update_id"):
            with self.subTest(key=key):
                state, metadata = fixture()
                del metadata[key]
                with self.assertRaisesRegex(ValueError, "MISSING_METADATA"):
                    reference_features(state, metadata)

    def test_invalid_replay_identity_type_is_rejected(self):
        for key, value in (("source_id", ""), ("session_id", 5), ("record_index", 0),
                           ("event_time_ms", -1), ("first_update_id", True),
                           ("final_update_id", None), ("local_update_id", D("12"))):
            with self.subTest(key=key):
                state, metadata = fixture()
                metadata[key] = value
                with self.assertRaisesRegex(ValueError, "INVALID_METADATA"):
                    reference_features(state, metadata)

    def test_pre_event_state_cannot_be_used(self):
        state, metadata = fixture()
        state["local_update_id"] = 10
        with self.assertRaisesRegex(ValueError, "LOCAL_UPDATE_ID_MISMATCH"):
            reference_features(state, metadata)

    def test_metadata_not_applied_to_event_is_rejected(self):
        state, metadata = fixture()
        metadata["local_update_id"] = 11
        with self.assertRaisesRegex(ValueError, "EVENT_NOT_APPLIED"):
            reference_features(state, metadata)

    def test_reversed_update_ids_are_rejected(self):
        state, metadata = fixture()
        metadata["first_update_id"] = 13
        with self.assertRaisesRegex(ValueError, "INVALID_UPDATE_ID_RANGE"):
            reference_features(state, metadata)

    def test_malformed_canonical_container_is_rejected(self):
        for state in (None, [], {"bids": {}, "asks": []}, {"bids": [["1"]], "asks": []}):
            with self.subTest(state=state), self.assertRaises(ValueError):
                reference_features(state, fixture()[1])

    def test_reference_has_no_main_formula_or_builder_import(self):
        from data_pipeline.features import reference
        tree = ast.parse(inspect.getsource(reference))
        imports = [node.module or "" for node in ast.walk(tree)
                   if isinstance(node, ast.ImportFrom)]
        imports += [alias.name for node in ast.walk(tree) if isinstance(node, ast.Import)
                    for alias in node.names]
        self.assertFalse(any("formulas" in name or "builder" in name for name in imports))

    def test_ordinary_canonical_book_state_is_accepted(self):
        state = {"local_update_id": 12,
                 "bids": {D(str(99 - i)): D(str(i + 1)) for i in range(5)},
                 "asks": {D(str(101 + i)): D(str(5 - i)) for i in range(5)}}
        self.assertEqual(reference_features(canonical_state(state), fixture()[1]), self.rows())



    def test_main_builder_matches_every_field_for_independent_artificial_books(self):
        from data_pipeline.features.builder import FeatureBuilder
        variants = [
            fixture(), fixture(bid_quantities=("1", "2", "3", "4")),
            fixture(ask_quantities=("5", "4")),
            fixture(bid_quantities=()), fixture(ask_quantities=()),
            fixture(bid_quantities=(), ask_quantities=()),
            fixture(bid_quantities=("1.123456789012345678901234567890123456789",
                                    "2.33333333333333333333333333333333333333",
                                    "0.000000000000000000000000001", "4", "5")),
        ]
        crossed, crossed_metadata = fixture()
        crossed["bids"][0][0] = "102"
        variants.append((crossed, crossed_metadata))
        for index, (state, metadata) in enumerate(variants):
            with self.subTest(variant=index):
                book = OrderBookRebuilder("artificial_session", "artificial_snapshot",
                                          "artificial_events")
                snapshot = Snapshot("artificial_snapshot", "artificial_session", 10,
                                    tuple((D(p), D(q)) for p, q in state["bids"]),
                                    tuple((D(p), D(q)) for p, q in state["asks"]))
                book.load_snapshot(snapshot)
                event = Event("artificial_events", "artificial_session", 1,
                              1000, 11, 12, (), ())
                self.assertEqual(book.apply_event(event)["action"], "APPLY")
                main = FeatureBuilder("artificial_events", "artificial_session",
                                      "replay").from_book(book, event)
                reference = reference_features(canonical_state(book.full_state()), metadata)
                for view in (A, T):
                    for field in fields(view):
                        self.assertEqual(reference[view][field], main[view][field],
                                         (index, view, field))

    def test_monkeypatch_main_builder_and_formulas_does_not_affect_reference(self):
        from data_pipeline.features.builder import FeatureBuilder
        from data_pipeline.features import formulas
        expected = self.rows()
        with patch.object(FeatureBuilder, "from_book", side_effect=AssertionError("main used")), \
             patch.object(formulas, "aggregate", side_effect=AssertionError("aggregate used")), \
             patch.object(formulas, "depth", side_effect=AssertionError("depth used")):
            self.assertEqual(self.rows(), expected)

    def test_changing_current_event_changes_features_without_future_input(self):
        from data_pipeline.features.builder import FeatureBuilder
        state, metadata = fixture()
        book = OrderBookRebuilder("artificial_session", "artificial_snapshot",
                                  "artificial_events")
        book.load_snapshot(Snapshot(
            "artificial_snapshot", "artificial_session", 10,
            tuple((D(p), D(q)) for p, q in state["bids"]),
            tuple((D(p), D(q)) for p, q in state["asks"])))
        builder = FeatureBuilder("artificial_events", "artificial_session", "replay")
        event = Event("artificial_events", "artificial_session", 1,
                      1000, 11, 12, ((D("99"), D("9")),), ())
        book.apply_event(event)
        main = builder.from_book(book, event)
        reference = reference_features(canonical_state(book.full_state()), metadata)
        self.assertEqual(main, reference)
        self.assertEqual(reference[T]["bid_quantity_1"], D("9"))
        self.assertNotEqual(reference[A]["obi_5"], self.rows()[A]["obi_5"])

    def test_high_precision_main_and_reference_are_caller_context_independent(self):
        from data_pipeline.features.builder import FeatureBuilder
        state, metadata = fixture(
            bid_quantities=("0.0000000000000001234567890123456789",
                            "1.0000000000000000000000000000000001", "2", "3", "4"))
        book = OrderBookRebuilder("artificial_session", "artificial_snapshot",
                                  "artificial_events")
        book.load_snapshot(Snapshot(
            "artificial_snapshot", "artificial_session", 10,
            tuple((D(p), D(q)) for p, q in state["bids"]),
            tuple((D(p), D(q)) for p, q in state["asks"])))
        event = Event("artificial_events", "artificial_session", 1,
                      1000, 11, 12, (), ())
        book.apply_event(event)
        canonical = canonical_state(book.full_state())
        expected = reference_features(canonical, metadata)
        with localcontext() as caller:
            caller.prec = 3
            caller.rounding = ROUND_DOWN
            caller.traps[Inexact] = True
            main = FeatureBuilder("artificial_events", "artificial_session",
                                  "replay").from_book(book, event)
            reference = reference_features(canonical, metadata)
        self.assertEqual(main, expected)
        self.assertEqual(reference, expected)


if __name__ == "__main__":
    unittest.main()


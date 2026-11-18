"""Artificial feature-row checks; no registered market data is opened."""

import copy
import json
import unittest
from decimal import Decimal, localcontext

from data_pipeline.features.schema import fields
from data_pipeline.features.validator import FeatureValidator, SOURCE_ABSOLUTE_TOLERANCE

D = Decimal


def aggregate(index=1):
    row = dict.fromkeys(fields("aggregate_core_v1"))
    row.update(schema_version="1.0", feature_view="aggregate_core_v1", source_id="fixture",
               session_id="session", record_index=index, event_time_ms=1000 + index,
               first_update_id=None, final_update_id=None, local_update_id=100 + index,
               best_bid=D("99"), best_ask=D("101"), mid_price=D("100"), spread=D("2"),
               spread_bps=D("200"), bid_volume_5=D("10"), ask_volume_5=D("5"),
               obi_5=D("0.33333333333333333333333333333333333333333333333333"),
               valid_feature_row=True, invalid_reason="")
    return row


def depth(index=1):
    row = dict.fromkeys(fields("depth_top5_v1"))
    row.update(schema_version="1.0", feature_view="depth_top5_v1", source_id="fixture",
               session_id="session", record_index=index, event_time_ms=1000 + index,
               first_update_id=100 + index, final_update_id=100 + index,
               local_update_id=100 + index, mid_price=D(100), spread=D(2),
               spread_bps=D(200), microprice=D("100.33333333333333333333333333333333333333333333333"),
               microprice_deviation_bps=D("33.333333333333333333333333333333333333333333333"),
               valid_feature_row=True, invalid_reason="")
    for i in range(1, 6):
        row.update({f"bid_price_{i}": D(100 - i), f"ask_price_{i}": D(100 + i),
                    f"bid_quantity_{i}": D(2), f"ask_quantity_{i}": D(1),
                    f"cumulative_bid_quantity_{i}": D(2 * i),
                    f"cumulative_ask_quantity_{i}": D(i),
                    f"bid_distance_bps_{i}": D(100 * i),
                    f"ask_distance_bps_{i}": D(100 * i),
                    f"level_imbalance_{i}": D("0.33333333333333333333333333333333333333333333333333")})
    for k in (1, 3, 5):
        row[f"obi_{k}"] = D("0.33333333333333333333333333333333333333333333333333")
    return row


def validator(view="aggregate_core_v1", kind="csv"):
    return FeatureValidator("fixture", "session", view, kind)


class FeatureValidatorTests(unittest.TestCase):
    def test_valid_aggregate_and_json_safe_summary(self):
        v = validator()
        row = v.observe(aggregate())
        self.assertTrue(row["valid_feature_row"])
        self.assertEqual(v.summary()["valid_feature_rows"], 1)
        json.dumps(v.summary(), allow_nan=False)

    def test_valid_depth(self):
        v = validator("depth_top5_v1", "replay")
        self.assertTrue(v.observe(depth())["valid_feature_row"])

    def test_csv_missing_update_ids_legitimate(self):
        row = aggregate()
        for key in ("first_update_id", "final_update_id", "local_update_id"):
            row[key] = None
        self.assertTrue(validator().observe(row)["valid_feature_row"])

    def test_replay_missing_ids_invalid(self):
        row = depth()
        for key in ("first_update_id", "final_update_id", "local_update_id"):
            row[key] = None
        result = validator("depth_top5_v1", "replay").observe(row)
        self.assertFalse(result["valid_feature_row"])
        self.assertIn("MISSING_EVENT_METADATA", result["invalid_reason"])

    def test_invalid_row_retained_and_input_not_mutated(self):
        row = aggregate()
        row.update(valid_feature_row=False, invalid_reason="CUSTOM")
        original = copy.deepcopy(row)
        v = validator()
        result = v.observe(row)
        self.assertEqual(row, original)
        self.assertFalse(result["valid_feature_row"])
        self.assertEqual(v.summary()["input_record_count"], 1)
        self.assertEqual(v.summary()["output_record_count"], 1)
        self.assertEqual(v.summary()["invalid_feature_rows"], 1)

    def test_cross_source_session_and_view_rejected(self):
        for name, value in (("source_id", "other"), ("session_id", "other"),
                            ("feature_view", "depth_top5_v1")):
            with self.subTest(name=name):
                row = aggregate()
                row[name] = value
                with self.assertRaises(ValueError):
                    validator().observe(row)

    def test_exact_schema_rejects_missing_or_extra(self):
        row = aggregate()
        row.pop("mid_price")
        with self.assertRaises(ValueError):
            validator().observe(row)
        row = aggregate()
        row["local_timestamp_us"] = 3
        with self.assertRaises(ValueError):
            validator().observe(row)

    def test_csv_depth_view_rejected(self):
        with self.assertRaises(ValueError):
            validator("depth_top5_v1", "csv")

    def test_crossed_book_invalid(self):
        row = aggregate()
        row.update(best_bid=D(102), best_ask=D(101))
        v = validator()
        self.assertFalse(v.observe(row)["valid_feature_row"])
        self.assertEqual(v.summary()["crossed_book_rows"], 1)

    def test_locked_book_invalid(self):
        row = aggregate()
        row.update(best_bid=D(101), best_ask=D(101), spread=D(0))
        result = validator().observe(row)
        self.assertIn("CROSSED_BOOK", result["invalid_reason"])
        self.assertIn("NONPOSITIVE_SPREAD", result["invalid_reason"])

    def test_empty_side_and_insufficient_depth(self):
        row = depth()
        row["bid_price_1"] = None
        v = validator("depth_top5_v1", "replay")
        result = v.observe(row)
        self.assertIn("EMPTY_BOOK_SIDE", result["invalid_reason"])
        self.assertEqual(v.summary()["insufficient_depth_rows"], 1)

    def test_zero_aggregate_denominator_invalid_not_forced_zero(self):
        row = aggregate()
        row.update(bid_volume_5=D(0), ask_volume_5=D(0), obi_5=None)
        v = validator()
        result = v.observe(row)
        self.assertIsNone(result["obi_5"])
        self.assertIn("ZERO_DEPTH_DENOMINATOR", result["invalid_reason"])
        self.assertEqual(v.summary()["zero_denominator_rows"], 1)

    def test_zero_level_denominator_warning_without_forced_imbalance(self):
        row = depth()
        row.update(bid_quantity_2=D(0), ask_quantity_2=D(0), level_imbalance_2=None)
        v = validator("depth_top5_v1", "replay")
        self.assertTrue(v.observe(row)["valid_feature_row"])
        self.assertEqual(v.summary()["quality_warnings"]["ZERO_LEVEL_DENOMINATOR:2"], 1)

    def test_zero_level_undefined_value_rejected(self):
        row = depth()
        row.update(bid_quantity_2=D(0), ask_quantity_2=D(0), level_imbalance_2=D(0))
        result = validator("depth_top5_v1", "replay").observe(row)
        self.assertIn("UNDEFINED_LEVEL_IMBALANCE_NOT_EMPTY", result["invalid_reason"])

    def test_builder_zero_level_warning_alone_stays_valid(self):
        row = depth()
        row.update(bid_quantity_2=D(0), ask_quantity_2=D(0), level_imbalance_2=None,
                   invalid_reason="ZERO_LEVEL_DENOMINATOR", valid_feature_row=True)
        result = validator("depth_top5_v1", "replay").observe(row)
        self.assertTrue(result["valid_feature_row"])
        self.assertEqual(result["invalid_reason"], "ZERO_LEVEL_DENOMINATOR")

    def test_negative_price_and_quantity_invalid(self):
        row = aggregate()
        row.update(best_bid=D(-1), bid_volume_5=D(-1))
        result = validator().observe(row)
        self.assertIn("INVALID_PRICE", result["invalid_reason"])
        self.assertIn("INVALID_QUANTITY", result["invalid_reason"])

    def test_nonfinite_replaced_with_null_and_counted(self):
        for value in ("NaN", "sNaN", "Infinity", "-Infinity"):
            row = aggregate()
            row["obi_5"] = D(value)
            v = validator()
            result = v.observe(row)
            self.assertIsNone(result["obi_5"])
            self.assertFalse(result["valid_feature_row"])
            self.assertEqual(v.summary()["non_finite_values"], 1)

    def test_float_not_accepted_as_formal_number(self):
        row = aggregate()
        row["mid_price"] = 100.0
        result = validator().observe(row)
        self.assertIsNone(result["mid_price"])
        self.assertIn("INVALID_NUMERIC_TYPE", result["invalid_reason"])

    def test_obi_out_of_range_count(self):
        row = aggregate()
        row["obi_5"] = D("1.0001")
        v = validator()
        self.assertFalse(v.observe(row)["valid_feature_row"])
        self.assertEqual(v.summary()["obi_out_of_range"], 1)

    def test_level_imbalance_out_of_range_count(self):
        row = depth()
        row["level_imbalance_3"] = D("-1.01")
        v = validator("depth_top5_v1", "replay")
        self.assertFalse(v.observe(row)["valid_feature_row"])
        self.assertEqual(v.summary()["level_imbalance_out_of_range"], 1)

    def test_microprice_out_of_spread_count(self):
        row = depth()
        row["microprice"] = D("101.01")
        v = validator("depth_top5_v1", "replay")
        self.assertFalse(v.observe(row)["valid_feature_row"])
        self.assertEqual(v.summary()["microprice_out_of_spread"], 1)

    def test_microprice_at_boundaries_allowed(self):
        for value in (D(99), D(101)):
            row = depth()
            row["microprice"] = value
            self.assertTrue(validator("depth_top5_v1", "replay").observe(row)["valid_feature_row"])

    def test_event_time_backwards_invalid(self):
        v = validator()
        v.observe(aggregate(2))
        self.assertIn("EVENT_TIME_BACKWARDS", v.observe(aggregate(1))["invalid_reason"])
        self.assertEqual(v.summary()["event_time_backwards"], 1)

    def test_duplicate_event_time_nonadjacent_invalid(self):
        v = validator()
        for index in (1, 2, 3):
            row = aggregate(index)
            if index == 3:
                row["event_time_ms"] = 1001
            result = v.observe(row)
        self.assertIn("DUPLICATE_EVENT_TIME", result["invalid_reason"])
        self.assertEqual(v.summary()["duplicate_event_time"], 1)

    def test_update_id_backwards_invalid(self):
        v = validator()
        v.observe(aggregate(1))
        row = aggregate(2)
        row["local_update_id"] = 100
        self.assertIn("UPDATE_ID_BACKWARDS", v.observe(row)["invalid_reason"])
        self.assertEqual(v.summary()["update_id_backwards"], 1)

    def test_tolerance_boundary_is_inclusive(self):
        row = aggregate()
        original = dict(row)
        original["mid_price"] += SOURCE_ABSOLUTE_TOLERANCE
        v = validator()
        self.assertTrue(v.observe(row, original)["valid_feature_row"])
        self.assertEqual(v.summary()["source_value_mismatch_count"], 0)
        self.assertEqual(v.summary()["maximum_source_value_difference"]["mid_price"], "0.00000001")

    def test_tolerance_exceeded_is_invalid_and_preserves_values(self):
        row = aggregate()
        source = dict(row)
        source["mid_price"] += D("0.000000010001")
        v = validator()
        result = v.observe(row, source)
        self.assertEqual(result["mid_price"], D(100))
        self.assertIn("SOURCE_VALUE_MISMATCH", result["invalid_reason"])
        self.assertEqual(v.summary()["source_value_mismatch_count"], 1)
        self.assertEqual(v.summary()["source_value_mismatch_rows"], 1)
        self.assertEqual(v.source_differences[0]["original"], "100.000000010001")

    def test_difference_distribution_and_bounded_samples(self):
        v = validator()
        for index in range(1, 26):
            row = aggregate(index)
            source = dict(row)
            source["spread"] += D("1e-11")
            v.observe(row, source)
        dist = v.summary()["source_value_differences"]["spread"]
        self.assertEqual(dist["count"], 25)
        self.assertEqual(dist["nonzero_count"], 25)
        self.assertEqual(dist["histogram"]["1e-12_to_1e-10_inclusive"], 25)
        self.assertEqual(len(dist["nonzero_samples"]), 20)
        self.assertEqual(dist["sum_absolute_difference"], "0.00000000025")

    def test_all_histogram_buckets_and_signed_difference(self):
        values = ("0", "1e-13", "1e-11", "1e-9", "1e-7")
        v = validator()
        for index, delta in enumerate(values, 1):
            row = aggregate(index)
            source = dict(row)
            source["spread"] -= D(delta)
            v.observe(row, source)
        dist = v.summary()["source_value_differences"]["spread"]
        self.assertEqual(list(dist["histogram"].values()), [1, 1, 1, 1, 1])
        self.assertTrue(dist["sum_signed_difference"].startswith("-"))

    def test_summary_independent_of_ambient_decimal_context(self):
        row = aggregate()
        original = dict(row)
        original["obi_5"] = D("0.33333333")
        a = validator()
        b = validator()
        a.observe(row, original)
        with localcontext() as ctx:
            ctx.prec = 4
            b.observe(row, original)
        self.assertEqual(a.summary(), b.summary())

    def test_invalid_reasons_unique_sorted(self):
        row = aggregate()
        row.update(valid_feature_row=False, invalid_reason="Z;A;Z")
        self.assertEqual(validator().observe(row)["invalid_reason"], "A;Z")

    def test_missing_values_count_and_not_dropped(self):
        row = aggregate()
        row["mid_price"] = None
        v = validator()
        result = v.observe(row)
        self.assertFalse(result["valid_feature_row"])
        self.assertEqual(v.summary()["missing_values_by_field"]["mid_price"], 1)
        self.assertEqual(v.summary()["output_record_count"], 1)

    def test_csv_local_timestamp_not_propagated_from_source_record(self):
        row = aggregate()
        source = dict(row, local_timestamp_us=999)
        result = validator().observe(row, source)
        self.assertNotIn("local_timestamp_us", result)
        self.assertNotIn("local_timestamp_us", json.dumps(validator().source_differences))

    def test_summary_all_requested_metrics_present(self):
        required = {"input_record_count", "output_record_count", "valid_feature_rows",
                    "invalid_feature_rows", "missing_values", "non_finite_values",
                    "crossed_book_rows", "insufficient_depth_rows", "zero_denominator_rows",
                    "obi_out_of_range", "level_imbalance_out_of_range",
                    "microprice_out_of_spread", "event_time_backwards",
                    "duplicate_event_time", "update_id_backwards",
                    "source_value_mismatch_count", "maximum_source_value_difference"}
        self.assertTrue(required <= set(validator().summary()))


if __name__ == "__main__":
    unittest.main()


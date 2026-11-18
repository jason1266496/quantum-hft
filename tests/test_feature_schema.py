"""Artificial contract tests; no market files are opened."""

import hashlib
import json
import unittest
from data_pipeline.features.schema import fields, feature_schema, schema_hash, VIEWS


class FeatureSchemaTests(unittest.TestCase):
    def test_aggregate_column_order(self):
        self.assertEqual(fields(VIEWS[0]), (
            "schema_version", "feature_view", "source_id", "session_id", "record_index",
            "event_time_ms", "first_update_id", "final_update_id", "local_update_id",
            "best_bid", "best_ask", "mid_price", "spread", "spread_bps", "bid_volume_5",
            "ask_volume_5", "obi_5", "valid_feature_row", "invalid_reason"))

    def test_depth_column_groups(self):
        names = fields(VIEWS[1])
        self.assertEqual(len(names), 64)
        self.assertEqual(names[9:14], tuple(f"bid_price_{i}" for i in range(1, 6)))
        self.assertEqual(names[14:19], tuple(f"bid_quantity_{i}" for i in range(1, 6)))
        self.assertEqual(names[-7:], ("mid_price", "spread", "spread_bps", "microprice", "microprice_deviation_bps", "valid_feature_row", "invalid_reason"))

    def test_fields_are_unique(self):
        for view in VIEWS:
            self.assertEqual(len(fields(view)), len(set(fields(view))))

    def test_no_prohibited_output_columns(self):
        for view in VIEWS:
            for name in fields(view):
                self.assertFalse(any(token in name for token in ("local_timestamp", "future", "target", "label", "rolling")))

    def test_views_do_not_mix(self):
        self.assertNotIn("bid_price_1", fields(VIEWS[0]))
        self.assertNotIn("best_bid", fields(VIEWS[1]))
        self.assertNotIn("bid_volume_5", fields(VIEWS[1]))

    def test_metadata_complete(self):
        required = {"name", "data_type", "nullable", "unit", "formula", "source", "allowed_range", "availability", "leakage_risk", "notes"}
        for view in VIEWS:
            self.assertEqual([item["name"] for item in feature_schema(view)["fields"]], list(fields(view)))
            for item in feature_schema(view)["fields"]:
                self.assertEqual(set(item), required)

    def test_exclusions_explicit(self):
        excluded = feature_schema(VIEWS[0])["excluded_fields"]
        self.assertEqual(excluded["local_timestamp_us"], "PROHIBITED")
        self.assertEqual(excluded["future_return"], "NOT_PRESENT")
        self.assertEqual(excluded["target_label"], "NOT_PRESENT")
        self.assertEqual(excluded["per_level_depth_on_csv"], "NOT_AVAILABLE")

    def test_schema_hash_stable_and_matches_bytes(self):
        for view in VIEWS:
            encoded = json.dumps(feature_schema(view), sort_keys=True, ensure_ascii=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
            self.assertEqual(schema_hash(view), hashlib.sha256(encoded).hexdigest())
            self.assertEqual(schema_hash(view), schema_hash(view))
        self.assertNotEqual(schema_hash(VIEWS[0]), schema_hash(VIEWS[1]))

    def test_returned_schema_does_not_mutate_contract(self):
        first = feature_schema(VIEWS[0])
        first["fields"][0]["name"] = "bad"
        first["field_order"].clear()
        self.assertEqual(feature_schema(VIEWS[0])["fields"][0]["name"], "schema_version")
        self.assertEqual(len(fields(VIEWS[0])), 19)

    def test_unknown_view_rejected(self):
        for operation in (fields, feature_schema, schema_hash):
            with self.assertRaisesRegex(ValueError, "UNKNOWN_FEATURE_VIEW"):
                operation("labels")

    def test_numeric_precision_policy_explicit(self):
        policy = feature_schema(VIEWS[0])["numeric_policy"]
        self.assertEqual(policy["precision"], 50)
        self.assertEqual(policy["rounding"], "ROUND_HALF_EVEN")
        self.assertIn("UNKNOWN", policy["source_rounding"])

    def test_event_time_is_metadata(self):
        row = next(item for item in feature_schema(VIEWS[0])["fields"] if item["name"] == "event_time_ms")
        self.assertEqual(row["leakage_risk"], "METADATA_NOT_MODEL_FEATURE")

    def test_csv_update_id_provenance_disclosed(self):
        row = next(item for item in feature_schema(VIEWS[0])["fields"] if item["name"] == "local_update_id")
        self.assertIn("UNKNOWN", " ".join(row["notes"]))
        self.assertIn("alias", " ".join(row["notes"]))


if __name__ == "__main__":
    unittest.main()

"""Artificial Phase 2A inspector tests. All temporary files stay beneath tests/."""
import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from tools.inspect_data_sources import inspect_sources, _policy, ADAPTERS, CSVAdapter

TESTS = Path(__file__).resolve().parent
CSV = ("local_timestamp_us,event_time_ms,update_id,best_bid,best_ask,mid_price,spread,bid_volume_5,ask_volume_5,obi_5\n"
       "1000000,1001,1,100,102,101,2,3,2,0.2\n"
       "1100000,1101,2,101,103,102,2,3,2,0.2\n")

# Deliberately artificial values; both fixtures use the same confirmed capture
# schema. Numeric JSON literals avoid a Python float serialization round trip.
REPLAY_1000 = ('{"eventTime":1001,"firstUpdateId":41,"finalUpdateId":42,'
               '"bids":[{"price":99.125,"quantity":2},{"price":98,"quantity":0}],'
               '"asks":[{"price":101.25,"quantity":3.5}]}\n')
REPLAY_50000 = ('{"eventTime":1101,"firstUpdateId":70,"finalUpdateId":72,'
                '"bids":[{"price":199.1234567890123456789,"quantity":0.125}],'
                '"asks":[{"price":201,"quantity":0},{"price":202.5,"quantity":4}]}\n')
SNAPSHOT = '{"lastUpdateId":40,"bids":[["99","2"]],"asks":[["101","3"]]}'


class InspectSourcesTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="phase2a_inspector_", dir=TESTS)
        self.base = Path(self.temporary.name)
        self.project = self.base / "project"
        self.hft = self.base / "hft"
        (self.project / "configs").mkdir(parents=True)
        (self.project / "docs").mkdir()
        (self.hft / "results").mkdir(parents=True)
        self.source = self.hft / "results" / "sample.csv"
        self.source.write_text(CSV, encoding="utf-8")
        self.config = {
            "schema_version": "1.0", "access_mode": "read_only",
            "hft_project": str(self.hft), "hft_results": str(self.hft / "results"),
            "handoff_directory": "reference/hft_phase1/20260101T000000Z",
            "phase1_v2_run_id": "20261018T210029Z",
            "timestamp_review_run_id": "20261018T212122Z",
            "allow_hft_write": False, "allow_network": False,
            "allow_real_trading": False, "allow_testnet_trading": False,
            "allow_cross_session_labels": False, "time_order_field": "event_time_ms",
            "local_timestamp_policy": "not_receive_time_do_not_use_for_latency",
            "sources": [self.record(self.source, "csv", "one_session")],
        }
        self.policy = {
            "ordering_field": "event_time_ms", "session_isolation": True,
            "cross_session_labels": False, "cross_file_labels": False,
            "local_timestamp_is_receive_time": False,
            "local_timestamp_allowed_as_feature": False,
            "local_timestamp_allowed_for_network_latency": False,
            "local_timestamp_allowed_for_tick_to_trade": False,
            "allow_final_holdout_for_selection": False,
            "record_actual_horizon": True, "record_match_error": True,
            "invalidate_on_large_gap": True, "invalidate_session_tail": True,
            "require_clock_source_metadata": True,
            "horizons_ms": [100, 200, 500, 1000],
            "required_label_fields": [
                "requested_horizon_ms", "actual_horizon_ms", "target_event_time_ms",
                "match_error_ms", "valid_label", "invalid_reason"],
            "max_match_error_ms": None,
            "selection_status": "TO_BE_DETERMINED_FROM_TRAINING_DATA_PROFILE_AND_RESEARCH_PROTOCOL",
        }
        self.config_path = self.project / "configs/data_sources.json"
        self.policy_path = self.project / "configs/timestamp_policy.json"
        self.flush()
        self.output = self.project / "artifacts/phase2a/20260101T000000Z"

    def tearDown(self):
        self.temporary.cleanup()

    def record(self, path, kind, session):
        payload = path.read_bytes()
        return {
            "relative_path": "results/" + path.name, "absolute_path": str(path),
            "file_type": kind, "sha256": hashlib.sha256(payload).hexdigest(),
            "size_bytes": len(payload), "audit_status": "PASS", "session_id": session,
            "event_time_start": 1001, "event_time_end": 1101,
            "allowed_uses": ["metadata_and_schema_inspection"],
            "prohibited_uses": ["source_write", "cross_session_labels", "network_latency"],
            "known_limitations": ["artificial_fixture"],
        }

    def flush(self):
        self.config_path.write_text(json.dumps(self.config), encoding="utf-8")
        self.policy_path.write_text(json.dumps(self.policy), encoding="utf-8")

    def add_source(self, name, payload, kind, session):
        path = self.hft / "results" / name
        path.write_text(payload, encoding="utf-8")
        record = self.record(path, kind, session)
        if kind == "snapshot":
            record["event_time_start"] = record["event_time_end"] = None
        self.config["sources"].append(record)
        return record

    def inspect(self, **kwargs):
        return inspect_sources(
            self.config_path, self.output, project_root=self.project,
            allowed_roots=(self.hft,), require_nine_sources=False,
            progress_stream=io.StringIO(), **kwargs)

    def test_normal_artifacts_and_bounded_sample(self):
        result = self.inspect(sample_records=1)
        self.assertEqual(result["status"], "PASS")
        self.assertFalse(result["full_scan"])
        self.assertEqual(result["rows"][0]["checked_records"], 1)
        for name in ("registry_snapshot.json", "source_validation.json",
                     "source_validation.csv", "adapter_summary.json", "command_history.txt"):
            self.assertTrue((self.output / name).is_file())
        self.assertFalse(result["raw_market_data_copied"])
        self.assertEqual(result["hash_scope"], "FULL_FILE_BYTES_STREAMED_REQUIRED_FOR_SHA256")

    def test_bad_hash_fails_and_does_not_parse(self):
        self.config["sources"][0]["sha256"] = "0" * 64
        self.flush()
        result = self.inspect()
        self.assertEqual(result["status"], "FAIL")
        self.assertEqual(result["rows"][0]["metadata_status"], "FAIL")
        self.assertEqual(result["rows"][0]["sha256_status"], "NOT_AVAILABLE")
        self.assertEqual(result["rows"][0]["size_status"], "NOT_AVAILABLE")
        self.assertIn("SHA-256 mismatch", result["rows"][0]["error"])
        self.assertEqual(result["rows"][0]["schema_status"], "NOT_AVAILABLE")

    def test_size_mismatch_fails(self):
        self.config["sources"][0]["size_bytes"] += 1
        self.flush()
        self.assertEqual(self.inspect()["status"], "FAIL")

    def test_existing_run_never_overwritten(self):
        self.output.mkdir(parents=True)
        sentinel = self.output / "sentinel.txt"
        sentinel.write_text("keep", encoding="utf-8")
        with self.assertRaises(FileExistsError):
            self.inspect()
        self.assertEqual(sentinel.read_text(), "keep")
        self.assertEqual(list(self.output.iterdir()), [sentinel])

    def test_existing_report_blocks_run(self):
        p = self.project / "docs/PHASE2A_REPORT_20260101T000000Z.md"
        p.write_text("keep", encoding="utf-8")
        with self.assertRaises(FileExistsError):
            self.inspect()
        self.assertFalse(self.output.exists())

    def test_output_outside_phase2a_rejected(self):
        self.output = self.project / "other/20260101T000000Z"
        with self.assertRaises(ValueError):
            self.inspect()
        self.assertFalse(self.output.exists())

    def test_output_symlink_rejected(self):
        outside = self.base / "outside"
        outside.mkdir()
        (self.project / "artifacts").mkdir()
        (self.project / "artifacts/phase2a").symlink_to(outside, target_is_directory=True)
        with self.assertRaises(ValueError):
            self.inspect()
        self.assertEqual(list(outside.iterdir()), [])

    def test_no_source_writes_or_lock_files(self):
        before_bytes = self.source.read_bytes()
        before = self.source.stat()
        names = sorted(str(p) for p in self.hft.rglob("*"))
        self.inspect()
        after = self.source.stat()
        self.assertEqual(self.source.read_bytes(), before_bytes)
        self.assertEqual((before.st_size, before.st_mtime_ns, before.st_ctime_ns, before.st_mode),
                         (after.st_size, after.st_mtime_ns, after.st_ctime_ns, after.st_mode))
        self.assertEqual(sorted(str(p) for p in self.hft.rglob("*")), names)

    def test_no_merge_between_sessions(self):
        second = self.hft / "results" / "other.csv"
        second.write_text(CSV, encoding="utf-8")
        self.config["sources"].append(self.record(second, "csv", "second_session"))
        self.flush()
        result = self.inspect(sample_records=1)
        self.assertEqual(result["status"], "PASS")
        self.assertEqual([r["session_id"] for r in result["rows"]], ["one_session", "second_session"])
        self.assertFalse(result["cross_file_merge_performed"])

    def test_receive_time_policy_rejected_before_output(self):
        self.policy["local_timestamp_is_receive_time"] = True
        self.flush()
        with self.assertRaises(ValueError):
            self.inspect()
        self.assertFalse(self.output.exists())

    def test_local_latency_policy_rejected(self):
        self.policy["local_timestamp_allowed_for_network_latency"] = True
        self.flush()
        with self.assertRaises(ValueError):
            self.inspect()

    def test_no_final_match_error_value(self):
        self.policy["max_match_error_ms"] = 25
        self.flush()
        with self.assertRaises(ValueError):
            self.inspect()

    def test_malformed_label_policy_rejected_before_output(self):
        for fields in (None, "requested_horizon_ms", [None], [{}]):
            with self.subTest(fields=fields):
                self.policy["required_label_fields"] = fields
                self.flush()
                with self.assertRaises(ValueError):
                    self.inspect()
                self.assertFalse(self.output.exists())

    def test_sample_does_not_claim_unsampled_rows_valid(self):
        bad = CSV + "broken,row\n"
        self.source.write_text(bad, encoding="utf-8")
        self.config["sources"][0] = self.record(self.source, "csv", "one_session")
        self.flush()
        result = self.inspect(sample_records=1)
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["rows"][0]["checked_records"], 1)
        self.assertTrue(any("unsampled" in warning for warning in result["warnings"]))

    def test_bad_sample_row_records_failure_location(self):
        self.source.write_text(CSV.splitlines()[0] + "\nbroken,row\n", encoding="utf-8")
        self.config["sources"][0] = self.record(self.source, "csv", "one_session")
        self.flush()
        result = self.inspect()
        self.assertEqual(result["status"], "FAIL")
        self.assertEqual(result["rows"][0]["schema_status"], "FAIL")
        self.assertEqual(result["parse_errors"], 1)
        self.assertIn("sample.csv", result["failure"])

    def test_full_scan_only_on_explicit_artificial_request(self):
        result = self.inspect(full_scan=True, sample_records=1)
        self.assertEqual(result["status"], "PASS")
        self.assertTrue(result["full_scan"])
        self.assertEqual(result["rows"][0]["checked_records"], 2)

    def test_invalid_sample_size_rejected(self):
        for invalid in (0, -1, True, 1.5):
            with self.subTest(invalid=invalid):
                with self.assertRaises(ValueError):
                    self.inspect(sample_records=invalid)
        self.assertFalse(self.output.exists())

    def test_hash_failure_does_not_parse_source_but_checks_later_source(self):
        second = self.hft / "results" / "later.csv"
        second.write_text(CSV, encoding="utf-8")
        self.config["sources"].append(self.record(second, "csv", "other_session"))
        self.config["sources"][0]["sha256"] = "0" * 64
        self.flush()
        result = self.inspect()
        self.assertEqual(result["status"], "FAIL")
        self.assertEqual(result["rows"][0]["schema_status"], "NOT_AVAILABLE")
        self.assertEqual(result["rows"][0]["checked_records"], 0)
        self.assertEqual(result["rows"][1]["status"], "PASS")
        self.assertEqual(result["rows"][1]["checked_records"], 2)
        self.assertEqual(result["rows"][1]["actual_sha256"], self.config["sources"][1]["sha256"])
        self.assertEqual(result["sources_checked"], 2)
        self.assertEqual(result["sources_failed"], 1)

    def test_inspector_handles_artificial_replay_1000_schema(self):
        self.config["sources"] = []
        self.add_source("artificial_replay_1000.jsonl", REPLAY_1000, "replay", "replay_one")
        self.flush()
        result = self.inspect()
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["rows"][0]["checked_records"], 1)
        summary = json.loads((self.output / "adapter_summary.json").read_text())["adapters"][0]["summary"]
        self.assertEqual(summary["schema_variant"], "capture_object_price_quantity_v1")

    def test_inspector_handles_artificial_replay_50000_same_schema(self):
        self.config["sources"] = []
        self.add_source("artificial_replay_50000.jsonl", REPLAY_50000, "replay", "replay_two")
        self.flush()
        result = self.inspect()
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["rows"][0]["checked_records"], 1)
        self.assertEqual(result["rows"][0]["size_status"], "PASS")
        summary = json.loads((self.output / "adapter_summary.json").read_text())["adapters"][0]["summary"]
        self.assertEqual(summary["schema_variant"], "capture_object_price_quantity_v1")

    def test_replay_sessions_remain_separate_with_same_schema(self):
        self.config["sources"] = []
        self.add_source("artificial_replay_1000.jsonl", REPLAY_1000, "replay", "replay_one")
        self.add_source("artificial_replay_50000.jsonl", REPLAY_50000, "replay", "replay_two")
        self.flush()
        result = self.inspect()
        self.assertEqual(result["status"], "PASS")
        self.assertEqual([r["session_id"] for r in result["rows"]], ["replay_one", "replay_two"])
        self.assertEqual([r["checked_records"] for r in result["rows"]], [1, 1])
        self.assertFalse(result["cross_file_merge_performed"])

    def test_wrong_replay_schema_fails_with_structured_location(self):
        event = json.loads(REPLAY_1000)
        event["bids"] = [[99, 2]]
        self.config["sources"] = []
        self.add_source("bad_replay.jsonl", json.dumps(event) + "\n", "replay", "bad_session")
        self.flush()
        result = self.inspect()
        row = result["rows"][0]
        self.assertEqual(result["status"], "FAIL")
        self.assertEqual(row["sha256_status"], "PASS")
        self.assertEqual(row["size_status"], "PASS")
        self.assertEqual(row["schema_status"], "FAIL")
        self.assertEqual(row["error_details"]["source_id"], "bad_replay")
        self.assertEqual(row["error_details"]["record_index"], 1)
        self.assertEqual(row["error_details"]["side"], "bids")
        self.assertEqual(row["error_details"]["update_index"], 0)
        self.assertIsInstance(row["error_details"]["safe_summary"], str)
        self.assertEqual(result["failures"][0]["error_details"], row["error_details"])

    def test_schema_failure_still_checks_later_source(self):
        self.source.write_text(CSV.splitlines()[0] + "\nbroken,row\n", encoding="utf-8")
        self.config["sources"][0] = self.record(self.source, "csv", "one_session")
        self.add_source("later.csv", CSV, "csv", "later_session")
        self.flush()
        result = self.inspect()
        self.assertEqual([r["status"] for r in result["rows"]], ["FAIL", "PASS"])
        self.assertEqual(result["rows"][1]["checked_records"], 2)
        self.assertEqual(result["parse_errors"], 1)

    def test_constructor_failure_is_isolated(self):
        class FailingFirstAdapter(CSVAdapter):
            def __init__(self, registry, source_id):
                if source_id == "sample":
                    raise RuntimeError("artificial constructor failure")
                super().__init__(registry, source_id)
        self.add_source("later.csv", CSV, "csv", "later_session")
        self.flush()
        with mock.patch.dict(ADAPTERS, {"csv": FailingFirstAdapter}):
            result = self.inspect()
        self.assertEqual([r["status"] for r in result["rows"]], ["FAIL", "PASS"])
        self.assertEqual(result["rows"][0]["error_details"]["phase"], "adapter_initialization")
        self.assertEqual(result["rows"][0]["sha256_status"], "NOT_AVAILABLE")

    def test_close_failure_is_isolated(self):
        class FailingFirstCloseAdapter(CSVAdapter):
            def close(self):
                super().close()
                if self.source.source_id == "sample":
                    raise OSError("artificial close failure")
        self.add_source("later.csv", CSV, "csv", "later_session")
        self.flush()
        with mock.patch.dict(ADAPTERS, {"csv": FailingFirstCloseAdapter}):
            result = self.inspect()
        self.assertEqual([r["status"] for r in result["rows"]], ["FAIL", "PASS"])
        self.assertEqual(result["rows"][0]["close_status"], "FAIL")
        self.assertEqual(result["rows"][0]["schema_status"], "PASS")
        self.assertEqual(result["rows"][0]["error_details"]["phase"], "close")

    def test_multiple_failures_are_preserved_and_valid_source_still_checked(self):
        self.config["sources"][0]["sha256"] = "0" * 64
        self.add_source("broken.csv", CSV.splitlines()[0] + "\nbroken,row\n", "csv", "broken_session")
        self.add_source("later.csv", CSV, "csv", "later_session")
        self.flush()
        result = self.inspect()
        self.assertEqual([r["status"] for r in result["rows"]], ["FAIL", "FAIL", "PASS"])
        self.assertEqual(result["sources_checked"], 3)
        self.assertEqual(result["sources_failed"], 2)
        self.assertEqual([entry["source_id"] for entry in result["failures"]], ["sample", "broken"])
        self.assertEqual(result["failure"], result["rows"][0]["error"])

    def test_nine_artificial_sources_checked_after_replay_schema_failure(self):
        self.config["sources"] = []
        for index in range(5):
            self.add_source(f"csv_{index}.csv", CSV, "csv", f"csv_session_{index}")
        self.add_source("snapshot_1000.json", SNAPSHOT, "snapshot", "pair_one")
        bad_event = json.loads(REPLAY_1000)
        bad_event["asks"] = [[101, 3]]
        self.add_source("replay_1000.jsonl", json.dumps(bad_event) + "\n", "replay", "pair_one")
        self.add_source("snapshot_50000.json", SNAPSHOT, "snapshot", "pair_two")
        self.add_source("replay_50000.jsonl", REPLAY_50000, "replay", "pair_two")
        self.flush()
        result = self.inspect(sample_records=100)
        self.assertEqual(result["status"], "FAIL")
        self.assertEqual(result["sources_checked"], 9)
        self.assertEqual(result["sources_passed"], 8)
        self.assertEqual(result["sources_failed"], 1)
        self.assertTrue(all(row["sha256_status"] == "PASS" for row in result["rows"]))
        self.assertTrue(all(row["size_status"] == "PASS" for row in result["rows"]))
        self.assertEqual([row["status"] for row in result["rows"]][6:], ["FAIL", "PASS", "PASS"])

    def test_config_path_escape_rejected(self):
        self.config_path = self.base / "elsewhere.json"
        self.config_path.write_text(json.dumps(self.config), encoding="utf-8")
        with self.assertRaises(ValueError):
            self.inspect()


if __name__ == "__main__":
    unittest.main()

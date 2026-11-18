"""Artificial-only integration tests for the Phase 2B CLI."""
import gzip
import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from tools.rebuild_orderbook import rebuild_pair, main, ReferenceOrderBookRebuilder

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "phase2b"
SNAPSHOT = '{"lastUpdateId":10,"bids":[["99","2"],["98","3"]],"asks":[["101","5"],["102","6"]]}'
EVENTS = [
    '{"eventTime":100,"firstUpdateId":8,"finalUpdateId":9,"bids":[],"asks":[]}',
    '{"eventTime":110,"firstUpdateId":10,"finalUpdateId":11,"bids":[{"price":99,"quantity":4}],"asks":[]}',
    '{"eventTime":120,"firstUpdateId":12,"finalUpdateId":12,"bids":[],"asks":[{"price":101,"quantity":7}]}',
    '{"eventTime":130,"firstUpdateId":12,"finalUpdateId":12,"bids":[],"asks":[]}',
    '{"eventTime":140,"firstUpdateId":12,"finalUpdateId":14,"bids":[{"price":98,"quantity":0}],"asks":[]}',
    '{"eventTime":150,"firstUpdateId":15,"finalUpdateId":15,"bids":[{"price":99,"quantity":0},{"price":99.25,"quantity":1.234567890123456789}],"asks":[]}',
]


class RebuildToolTests(unittest.TestCase):
    def setUp(self):
        FIXTURES.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=FIXTURES, prefix="artificial_")
        self.base = Path(self.temp.name)
        self.project = self.base / "project"
        self.hft = self.base / "artificial_input"
        (self.project / "configs").mkdir(parents=True)
        (self.hft / "results").mkdir(parents=True)
        self.sid = "replay_snapshot_1000"
        self.rid = "replay_events_1000"
        self.snapshot = self.hft / "results" / (self.sid + ".json")
        self.replay = self.hft / "results" / (self.rid + ".jsonl")
        self.snapshot.write_text(SNAPSHOT)
        self.replay.write_text("\n".join(EVENTS) + "\n")
        self.config_path = self.project / "configs/data_sources.json"
        self.config = {
            "schema_version": "1.0", "access_mode": "read_only",
            "hft_project": str(self.hft), "hft_results": str(self.hft / "results"),
            "allow_hft_write": False, "allow_network": False, "allow_real_trading": False,
            "allow_testnet_trading": False, "allow_cross_session_labels": False,
            "time_order_field": "event_time_ms",
            "local_timestamp_policy": "not_receive_time_do_not_use_for_latency", "sources": [],
        }
        self.flush()
        self.output = self.project / "artifacts/phase2b/20260101T000000Z/replay_1000"

    def tearDown(self):
        self.temp.cleanup()

    def flush(self):
        self.config["sources"] = [
            {"source_id": sid, "relative_path": "results/" + p.name,
             "absolute_path": str(p), "file_type": kind,
             "sha256": hashlib.sha256(p.read_bytes()).hexdigest(), "size_bytes": p.stat().st_size,
             "audit_status": "PASS", "session_id": "artificial_pair",
             "event_time_start": None if kind == "snapshot" else 100,
             "event_time_end": None if kind == "snapshot" else 150,
             "allowed_uses": ["artificial_book_test"], "prohibited_uses": ["source_write"],
             "known_limitations": ["artificial_only"]}
            for sid, p, kind in ((self.sid, self.snapshot, "snapshot"), (self.rid, self.replay, "replay"))]
        self.config_path.write_text(json.dumps(self.config))

    def run_pair(self, **kwargs):
        params = dict(compare_reference=True, repeat=2, progress_every=1,
                      project_root=self.project, allowed_roots=(self.hft,),
                      require_nine_sources=False, progress_stream=io.StringIO())
        params.update(kwargs)
        return rebuild_pair(self.config_path, self.sid, self.rid, self.output, **params)

    def read(self, name):
        return json.loads((self.output / name).read_text())

    def test_complete_pair_and_all_artifacts(self):
        result = self.run_pair()
        self.assertEqual(result["status"], "PASS")
        self.assertEqual([a["record_count"] for a in result["attempts"]], [6, 6])
        for name in ("source_validation.json", "continuity_summary.json", "continuity_events.csv",
                     "rebuild_summary.json", "checkpoint_state_hashes.csv", "top_levels_checkpoints.jsonl",
                     "final_book_summary.json", "final_book_state.json.gz", "reference_comparison.json",
                     "deterministic_repeat.json", "stdout.txt", "stderr.txt"):
            self.assertTrue((self.output / name).is_file(), name)
        with gzip.open(self.output / "final_book_state.json.gz", "rt") as stream:
            book = json.load(stream)
        self.assertEqual(book["local_update_id"], 15)
        self.assertEqual(book["bids"][0], ["99.25", "1.234567890123456789"])

    def test_stale_duplicate_overlap_and_bridge(self):
        first = self.run_pair()["attempts"][0]
        self.assertTrue(first["bridge_pass"])
        self.assertEqual(first["applied_events"], 4)
        self.assertEqual(first["stale_events"], 1)
        self.assertEqual(first["duplicate_events"], 1)
        self.assertEqual(first["overlapping_events"], 2)
        self.assertEqual(first["gaps"], 0)

    def test_each_applied_event_full_comparison(self):
        result = self.run_pair()
        self.assertEqual(result["attempts"][0]["reference_light_checks"], 6)
        self.assertGreaterEqual(result["attempts"][0]["reference_full_checks"], 5)

    def test_50000_pair_supported_same_schema(self):
        # Rename only artificial test files within this temporary fixture.
        self.sid, self.rid = "replay_snapshot_50000", "replay_events_50000"
        self.snapshot = self.hft / "results" / (self.sid + ".json")
        self.replay = self.hft / "results" / (self.rid + ".jsonl")
        self.snapshot.write_text(SNAPSHOT)
        self.replay.write_text("\n".join(EVENTS) + "\n")
        self.flush()
        self.output = self.output.parent / "replay_50000"
        result = self.run_pair()
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["attempts"][0]["reference_light_checks"], 6)
        checkpoints = (self.output / "checkpoint_state_hashes.csv").read_text()
        self.assertIn("INITIAL_SNAPSHOT", checkpoints)
        self.assertIn("FINAL", checkpoints)

    def test_all_required_50000_checkpoints_and_periodic_checks(self):
        self.sid, self.rid = "replay_snapshot_50000", "replay_events_50000"
        self.snapshot = self.hft / "results" / (self.sid + ".json")
        self.replay = self.hft / "results" / (self.rid + ".jsonl")
        self.snapshot.write_text(SNAPSHOT)
        # 25,001 tiny artificial events, without retaining event objects.
        with self.replay.open("w") as f:
            for index in range(1, 25002):
                f.write(json.dumps({"eventTime": index, "firstUpdateId": 10+index,
                                    "finalUpdateId": 10+index, "bids": [], "asks": []})+"\n")
        self.flush()
        self.output = self.output.parent / "replay_50000"
        result = self.run_pair(progress_every=10000)
        self.assertEqual(result["status"], "PASS")
        import csv
        with (self.output / "checkpoint_state_hashes.csv").open() as f:
            rows = [r for r in csv.DictReader(f) if r["repeat"] == "1"]
        indices = {int(r["record_index"]) for r in rows}
        self.assertTrue({0, 1, 10, 100, 1000, 5000, 10000, 25000, 25001} <= indices)
        self.assertTrue(set(range(1000, 25001, 1000)) <= indices)

    def test_input_contents_and_metadata_unchanged(self):
        def state():
            return {p.name: (p.read_bytes(), p.stat().st_mtime_ns, p.stat().st_ctime_ns)
                    for p in self.hft.rglob("*") if p.is_file()}
        before = state()
        self.run_pair()
        self.assertEqual(before, state())

    def test_existing_output_refused(self):
        self.output.mkdir(parents=True)
        marker = self.output / "keep"
        marker.write_text("unchanged")
        with self.assertRaises(FileExistsError):
            self.run_pair()
        self.assertEqual(marker.read_text(), "unchanged")
        self.assertEqual(list(self.output.iterdir()), [marker])

    def test_hft_output_rejected_without_write(self):
        self.output = self.hft / "results/output"
        with self.assertRaises(ValueError):
            self.run_pair()
        self.assertFalse(self.output.exists())

    def test_symlink_output_rejected(self):
        link = self.project / "artifacts"
        link.symlink_to(self.hft, target_is_directory=True)
        with self.assertRaises(ValueError):
            self.run_pair()
        self.assertFalse((self.hft / "phase2b").exists())

    def test_cross_pair_rejected(self):
        with self.assertRaises(ValueError):
            rebuild_pair(self.config_path, self.sid, "replay_events_50000", self.output,
                         project_root=self.project, allowed_roots=(self.hft,), require_nine_sources=False)
        self.assertFalse(self.output.exists())

    def test_cross_session_rejected(self):
        self.config["sources"][1]["session_id"] = "other"
        self.config_path.write_text(json.dumps(self.config))
        with self.assertRaises(ValueError):
            self.run_pair()
        self.assertFalse(self.output.exists())

    def test_csv_source_rejected(self):
        with self.assertRaises(ValueError):
            rebuild_pair(self.config_path, "csv_snapshot", "csv_events", self.output,
                         project_root=self.project, allowed_roots=(self.hft,), require_nine_sources=False)

    def test_hash_mismatch_fails_before_book(self):
        self.config["sources"][1]["sha256"] = "0" * 64
        self.config_path.write_text(json.dumps(self.config))
        result = self.run_pair()
        self.assertEqual(result["status"], "FAIL")
        self.assertEqual(result["attempts"], [])
        self.assertEqual(self.read("source_validation.json")["status"], "FAIL")

    def test_size_mismatch_fails(self):
        self.config["sources"][0]["size_bytes"] += 1
        self.config_path.write_text(json.dumps(self.config))
        self.assertEqual(self.run_pair()["status"], "FAIL")

    def test_first_bridge_failure_stops(self):
        self.replay.write_text(EVENTS[-1] + "\n")
        self.flush()
        result = self.run_pair()
        self.assertEqual(result["status"], "FAIL")
        self.assertEqual(result["attempts"][0]["bridge_failures"], 1)
        self.assertFalse(result["attempts"][0]["fully_consumed"])

    def test_gap_stops_before_following_events(self):
        self.replay.write_text(EVENTS[1] + "\n" + EVENTS[-1] + "\n" + EVENTS[2] + "\n")
        self.flush()
        result = self.run_pair()
        self.assertEqual(result["status"], "FAIL")
        self.assertEqual(result["attempts"][0]["record_count"], 2)
        self.assertEqual(result["attempts"][0]["gaps"], 1)
        self.assertEqual(result["attempts"][0]["final_summary"]["local_update_id"], 11)

    def test_bad_json_fails_with_location(self):
        self.replay.write_text(EVENTS[1] + "\n{broken\n" + EVENTS[2] + "\n")
        self.flush()
        first = self.run_pair()["attempts"][0]
        self.assertEqual(first["parse_errors"], 1)
        self.assertEqual(first["error"]["record_index"], 2)
        self.assertFalse(first["fully_consumed"])

    def test_invalid_price_and_quantity_are_counted(self):
        for field, value in (("price", 0), ("quantity", -1)):
            with self.subTest(field=field):
                self.output = self.project / ("artifacts/phase2b/20260101T00000"+str(int(value == -1))+"Z/replay_1000")
                update = {"price": 99, "quantity": 1}
                update[field] = value
                self.replay.write_text(json.dumps({"eventTime": 100, "firstUpdateId": 11, "finalUpdateId": 11,
                                                  "bids": [update], "asks": []})+"\n")
                self.flush()
                first = self.run_pair()["attempts"][0]
                self.assertEqual(first["invalid_"+field], 1)

    def test_structure_error_does_not_invent_numeric_failure(self):
        self.replay.write_text('{"eventTime":100,"firstUpdateId":11,"finalUpdateId":11,"bids":[{"price":99}],"asks":[]}\n')
        self.flush()
        first = self.run_pair()["attempts"][0]
        self.assertEqual(first["parse_errors"], 1)
        self.assertEqual(first["invalid_price"], 0)
        self.assertEqual(first["invalid_quantity"], 0)

    def test_second_snapshot_failure_does_not_reuse_first_metadata(self):
        from tools.rebuild_orderbook import _snapshot, SourceValidationError
        calls = 0
        def fail_second(adapter):
            nonlocal calls
            calls += 1
            if calls == 2:
                raise SourceValidationError("artificial source changed")
            return _snapshot(adapter)
        with mock.patch("tools.rebuild_orderbook._snapshot", fail_second):
            result = self.run_pair()
        self.assertEqual(result["status"], "FAIL")
        self.assertIsNone(result["attempts"][1]["snapshot_last_update_id"])
        self.assertEqual(self.read("source_validation.json")["status"], "FAIL")

    def test_crossed_and_empty_are_quality_failures(self):
        self.replay.write_text('{"eventTime":100,"firstUpdateId":11,"finalUpdateId":11,"bids":[{"price":103,"quantity":1}],"asks":[]}\n')
        self.flush()
        first = self.run_pair()["attempts"][0]
        self.assertEqual(first["status"], "FAIL")
        self.assertEqual(first["crossed_book_count"], 1)

    def test_empty_book_quality_failure(self):
        self.replay.write_text('{"eventTime":100,"firstUpdateId":11,"finalUpdateId":11,"bids":[{"price":99,"quantity":0},{"price":98,"quantity":0}],"asks":[]}\n')
        self.flush()
        first = self.run_pair()["attempts"][0]
        self.assertEqual(first["status"], "FAIL")
        self.assertEqual(first["empty_side_count"], 1)

    def test_local_timestamp_is_not_consumed(self):
        event = json.loads(EVENTS[1])
        event["local_timestamp_us"] = 999
        self.replay.write_text(json.dumps(event)+"\n")
        self.flush()
        result = self.run_pair()
        self.assertEqual(result["status"], "FAIL")
        self.assertEqual(result["attempts"][0]["parse_errors"], 1)

    def test_reference_mismatch_records_difference(self):
        original = ReferenceOrderBookRebuilder.full_state
        def different(book):
            from decimal import Decimal
            state = original(book)
            state["bids"][Decimal("1")] = Decimal("1")
            return state
        with mock.patch.object(ReferenceOrderBookRebuilder, "full_state", different):
            result = self.run_pair()
        self.assertEqual(result["status"], "FAIL")
        self.assertTrue(list(self.output.glob("reference_mismatch_*.json")))
        self.assertEqual(self.read("reference_comparison.json")["status"], "FAIL")

    def test_missing_reference_or_repeat_cannot_claim_pass(self):
        result = self.run_pair(compare_reference=False, repeat=1)
        self.assertEqual(result["status"], "FAIL")
        self.assertEqual(result["reference_status"], "NOT_AVAILABLE")
        self.assertEqual(result["deterministic_status"], "NOT_AVAILABLE")

    def test_progress_does_not_change_results(self):
        stream = io.StringIO()
        a = self.run_pair(progress_every=1, progress_stream=stream)
        self.output = self.project / "artifacts/phase2b/20260101T000001Z/replay_1000"
        b = self.run_pair(progress_every=1000)
        self.assertEqual(a["attempts"][0]["final_state_hash"], b["attempts"][0]["final_state_hash"])
        self.assertEqual(a["attempts"][0]["classification_counts"], b["attempts"][0]["classification_counts"])
        rows = [json.loads(line) for line in stream.getvalue().splitlines()]
        self.assertEqual(rows[-1]["percent"], 100.0)
        self.assertEqual(rows[-1]["event_count"], 6)
        self.assertEqual(rows[-1]["eta_seconds"], 0)

    def test_parameter_validation(self):
        for kwargs in ({"repeat": 0}, {"progress_every": 0}, {"compare_reference": "yes"}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                self.run_pair(**kwargs)
        self.assertFalse(self.output.exists())


if __name__ == "__main__":
    unittest.main()


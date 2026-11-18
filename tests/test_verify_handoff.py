"""Artificial-fixture tests only. Temporary data stays below this tests directory."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from tools.handoff_guard import create_unique_handoff_run, initialize_empty_root
from tools.verify_handoff import (
    EXPERIMENT_FALSE, EXPERIMENT_TRUE, MARKET_NAMES, POLICY_FALSE, POLICY_TRUE,
    REQUIRED_LABEL_FIELDS,
    RUN_IDS, SELECTION_STATUS, verify_handoff,
)


class VerifyHandoffTests(unittest.TestCase):
    def setUp(self):
        # The fixtures never name a real market input as a path to open.
        self.temporary = tempfile.TemporaryDirectory(
            prefix="handoff_fixture_", dir=Path(__file__).parent)
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name)
        self.source = self.base / "source"
        self.project = self.base / "project"
        (self.source / "docs").mkdir(parents=True)
        (self.project / "configs").mkdir(parents=True)
        self.run_id = "20261018T214147Z"
        self.run = create_unique_handoff_run(self.project, self.run_id)
        (self.run / "reports").mkdir()
        self.source_file = self.source / "docs/evidence.md"
        self.destination_file = self.run / "reports/evidence.md"
        payload = b"# Artificial audit\nNo real market inputs are opened.\n"
        self.source_file.write_bytes(payload)
        self.destination_file.write_bytes(payload)
        digest = hashlib.sha256(payload).hexdigest()
        self.copy = {
            "source_absolute_path": str(self.source_file),
            "source_relative_path": "docs/evidence.md",
            "destination_relative_path": self.destination_file.relative_to(self.project).as_posix(),
            "source_sha256": digest, "destination_sha256": digest,
            "source_size_bytes": len(payload), "destination_size_bytes": len(payload),
            "copy_status": "PASS",
        }
        self.manifest = {
            "schema_version": "1.0", "handoff_run_id": self.run_id,
            "created_at_utc": "2026-10-18T21:41:47Z",
            "source_project": str(self.source), "destination_project": str(self.project),
            **RUN_IDS, "phase1_v2_status": "PASS", "timestamp_review_status": "WARNING",
            "phase2_decision": "PASS_WITH_RESTRICTIONS",
            "copied_files": [self.copy], "missing_files": [],
            "excluded_paths": ["src/", "results/", "all raw market inputs"],
            "read_only_input_paths": [
                str(self.source / "results" / name) for name in sorted(MARKET_NAMES)
            ],
            "copied_file_count": 1, "copied_total_size_bytes": len(payload),
            "all_hashes_match": True, "hft_source_modified": False,
            "network_activity_performed": False, "trading_activity_performed": False,
            "model_training_performed": False,
        }
        self.manifest_path = self.run / "HANDOFF_MANIFEST.json"
        self.data = {
            "schema_version": "1.0", "access_mode": "read_only",
            "hft_project": str(self.source), "hft_results": str(self.source / "results"),
            "handoff_directory": self.run.relative_to(self.project).as_posix(),
            "phase1_v2_run_id": RUN_IDS["phase1_v2_run_id"],
            "timestamp_review_run_id": RUN_IDS["timestamp_review_run_id"],
            "allow_hft_write": False, "allow_network": False, "allow_real_trading": False,
            "allow_testnet_trading": False, "allow_cross_session_labels": False,
            "time_order_field": "event_time_ms",
            "local_timestamp_policy": "not_receive_time_do_not_use_for_latency",
            "sources": [{
                "relative_path": f"results/{name}",
                "absolute_path": str(self.source / "results" / name),
                "file_type": Path(name).suffix[1:],
                "sha256": "0" * 64, "size_bytes": 1,
                "audit_status": "PASS", "session_id": "NOT_AVAILABLE",
                "event_time_start": None, "event_time_end": None,
                "allowed_uses": ["future approved offline research"],
                "prohibited_uses": ["network latency"],
                "known_limitations": ["artificial metadata; no raw file exists"],
            } for name in sorted(MARKET_NAMES)],
        }
        self.policy = {
            "ordering_field": "event_time_ms",
            **{key: False for key in POLICY_FALSE},
            **{key: True for key in POLICY_TRUE},
            "max_match_error_ms": None, "selection_status": SELECTION_STATUS,
            "large_gap_threshold_ms": None, "horizons_ms": [100, 200, 500, 1000],
            "required_label_fields": sorted(REQUIRED_LABEL_FIELDS),
        }
        self.experiment = {
            **{key: False for key in EXPERIMENT_FALSE},
            **{key: True for key in EXPERIMENT_TRUE},
            "scaler_fit": "training_only", "current_execution_seed": None,
            "max_match_error_ms": None,
        }
        self.save_configs()

    def save_json(self, path, value):
        path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")

    def save_configs(self):
        self.save_json(self.manifest_path, self.manifest)
        self.save_json(self.project / "configs/data_sources.json", self.data)
        self.save_json(self.project / "configs/timestamp_policy.json", self.policy)
        self.save_json(self.project / "configs/experiment_defaults.json", self.experiment)

    def verify(self):
        return verify_handoff(
            self.manifest_path, project_root=self.project,
            expected_source_project=self.source,
            expected_destination_project=self.project)

    def assert_failed(self, text=None):
        result = self.verify()
        self.assertEqual(result.status, "FAIL", result.checks)
        self.assertEqual(result.exit_code, 1)
        if text:
            self.assertTrue(any(text in item["detail"] for item in result.failures),
                            result.checks)
        return result

    def test_normal_handoff_passes_without_opening_raw_inputs(self):
        self.assertFalse((self.source / "results").exists())
        before = self.destination_file.read_bytes()
        result = self.verify()
        self.assertTrue(result.ok, result.checks)
        self.assertEqual(result.exit_code, 0)
        self.assertTrue(result.warnings)  # Timestamp Review remains WARNING.
        self.assertEqual(self.destination_file.read_bytes(), before)
        self.assertFalse((self.source / "results").exists())

    def test_missing_destination_fails(self):
        self.destination_file.unlink()
        self.assert_failed()

    def test_sha256_mismatch_fails(self):
        self.destination_file.write_text("tampered evidence", encoding="utf-8")
        self.assert_failed("SHA-256 differ")

    def test_allow_hft_write_true_fails(self):
        self.data["allow_hft_write"] = True
        self.save_configs()
        self.assert_failed("allow_hft_write")

    def test_allow_network_true_fails(self):
        self.data["allow_network"] = True
        self.save_configs()
        self.assert_failed("allow_network")

    def test_allow_real_trading_true_fails(self):
        self.data["allow_real_trading"] = True
        self.save_configs()
        self.assert_failed("allow_real_trading")

    def test_allow_testnet_trading_true_fails(self):
        self.data["allow_testnet_trading"] = True
        self.save_configs()
        self.assert_failed("allow_testnet_trading")

    def test_receive_timestamp_claim_fails(self):
        self.policy["local_timestamp_is_receive_time"] = True
        self.save_configs()
        self.assert_failed("local_timestamp_is_receive_time")

    def test_dotenv_fails(self):
        (self.project / ".env").write_text("COMMENT=artificial\n", encoding="utf-8")
        self.assert_failed("secret/certificate/archive/model")

    def test_elf_magic_fails_with_innocent_extension(self):
        (self.project / "notes.txt").write_bytes(bytes((127, 69, 76, 70)) + b"synthetic")
        self.assert_failed("ELF executable magic")

    def test_copied_src_directory_fails(self):
        (self.project / "src").mkdir()
        (self.project / "src/fake.cpp").write_text("// artificial\n", encoding="utf-8")
        self.assert_failed("forbidden copied/source/build")

    def test_copied_results_directory_fails(self):
        (self.project / "results").mkdir()
        self.assert_failed("forbidden copied/source/build")

    def test_existing_handoff_run_cannot_be_overwritten(self):
        marker = self.run / "unchanged.txt"
        marker.write_text("preserve me", encoding="utf-8")
        with self.assertRaises(FileExistsError):
            create_unique_handoff_run(self.project, self.run_id)
        self.assertEqual(marker.read_text(encoding="utf-8"), "preserve me")

    def test_nonempty_project_cannot_be_initialized(self):
        marker = self.project / "unchanged.txt"
        marker.write_text("preserve root", encoding="utf-8")
        with self.assertRaises(FileExistsError):
            initialize_empty_root(self.project)
        self.assertEqual(marker.read_text(encoding="utf-8"), "preserve root")

    def test_path_traversal_copy_fails(self):
        self.copy["destination_relative_path"] = "../escape.md"
        self.save_configs()
        self.assert_failed("traversal")

    def test_symlink_destination_fails(self):
        self.destination_file.unlink()
        self.destination_file.symlink_to(self.source_file)
        self.assert_failed()

    def test_symlink_source_parent_fails(self):
        moved = self.source / "actual_docs"
        (self.source / "docs").rename(moved)
        (self.source / "docs").symlink_to(moved, target_is_directory=True)
        self.assert_failed()

    def test_missing_security_field_is_not_treated_as_false(self):
        del self.data["allow_network"]
        self.save_configs()
        self.assert_failed("missing required field: allow_network")

    def test_integer_zero_is_not_boolean_false(self):
        self.data["allow_network"] = 0
        self.save_configs()
        self.assert_failed("must be boolean")

    def test_match_error_must_remain_unselected(self):
        self.policy["max_match_error_ms"] = 25
        self.save_configs()
        self.assert_failed("max_match_error_ms")

    def test_literal_credential_assignment_fails(self):
        # Construct a synthetic fixture; do not embed a credential binding in this source.
        name = "api_" + "key"
        fake = "SYNTHETIC" + "CREDENTIAL123456789"
        (self.project / "settings.json").write_text(
            json.dumps({name: fake}), encoding="utf-8")
        self.assert_failed("credential-like assignment")

    def test_mentions_and_placeholders_are_not_credentials(self):
        (self.project / "safety.md").write_text(
            "API Key and Secret Key are forbidden; ELF and .env are checked.\n",
            encoding="utf-8")
        name = "api_" + "key"
        (self.project / "example.json").write_text(
            json.dumps({name: "YOUR_" + "API_KEY"}), encoding="utf-8")
        result = self.verify()
        self.assertTrue(result.ok, result.checks)

    def test_private_key_block_fails(self):
        header = "-----BEGIN " + "PRIVATE KEY-----"
        footer = "-----END " + "PRIVATE KEY-----"
        (self.project / "hidden.txt").write_text(
            header + "\nsynthetic fixture\n" + footer + "\n", encoding="utf-8")
        self.assert_failed("private-key/certificate block")

    def test_disguised_raw_csv_content_fails(self):
        (self.project / "hidden.txt").write_text(
            ",".join(("local_timestamp_us", "event_time_ms", "best_bid", "best_ask"))
            + "\n1000,1,2,3\n", encoding="utf-8")
        self.assert_failed("raw market record format")

    def test_disguised_snapshot_content_fails(self):
        (self.project / "hidden.json").write_text(json.dumps({
            "lastUpdateId": 1, "bids": [["1", "2"]], "asks": [["3", "4"]]
        }), encoding="utf-8")
        self.assert_failed("raw market record format")

    def test_market_snippet_inside_evidence_is_not_raw(self):
        (self.project / "snippet.json").write_text(json.dumps({
            "audit_example": {"lastUpdateId": 1, "bids": [], "asks": []}
        }), encoding="utf-8")
        result = self.verify()
        self.assertTrue(result.ok, result.checks)

    def test_unlisted_summary_csv_is_forbidden(self):
        (self.project / "csv_timestamp_summary.csv").write_text(
            "dataset,rows\nsynthetic,1\n", encoding="utf-8")
        self.assert_failed("hash-verified summary CSV")

    def test_manifest_whitelisted_derived_summary_passes(self):
        relative = (
            "artifacts/phase1_timestamp_review/"
            + RUN_IDS["timestamp_review_run_id"]
            + "/csv_timestamp_summary.csv")
        source = self.source / relative
        source.parent.mkdir(parents=True)
        payload = b"dataset,row_count\nsynthetic,1\n"
        source.write_bytes(payload)
        destination = self.run / "timestamp_review/csv_timestamp_summary.csv"
        destination.parent.mkdir()
        destination.write_bytes(payload)
        digest = hashlib.sha256(payload).hexdigest()
        self.manifest["copied_files"].append({
            "source_absolute_path": str(source), "source_relative_path": relative,
            "destination_relative_path": destination.relative_to(self.project).as_posix(),
            "source_sha256": digest, "destination_sha256": digest,
            "source_size_bytes": len(payload), "destination_size_bytes": len(payload),
            "copy_status": "PASS",
        })
        self.manifest["copied_file_count"] += 1
        self.manifest["copied_total_size_bytes"] += len(payload)
        self.save_configs()
        result = self.verify()
        self.assertTrue(result.ok, result.checks)

    def test_source_market_path_is_rejected_before_open(self):
        # No market file is created. The copy whitelist rejects metadata first.
        self.copy["source_relative_path"] = "results/replay_snapshot_1000.json"
        self.copy["source_absolute_path"] = str(
            self.source / self.copy["source_relative_path"])
        self.save_configs()
        self.assert_failed("approved docs/artifacts evidence")

    def test_disabled_experiment_gate_cannot_be_enabled(self):
        self.experiment["allow_model_training"] = True
        self.save_configs()
        self.assert_failed("allow_model_training")

    def test_missing_manifest_field_fails(self):
        del self.manifest["hft_source_modified"]
        self.save_configs()
        self.assert_failed("missing manifest fields")

    def test_tampered_recorded_digest_fails(self):
        self.copy["source_sha256"] = "f" * 64
        self.save_configs()
        self.assert_failed("recorded digest")

    def test_absent_and_empty_initialization_are_accepted(self):
        target = self.base / "new_empty_project"
        self.assertEqual(initialize_empty_root(target), target)
        self.assertEqual(initialize_empty_root(target), target)

    def test_symlink_root_initialization_is_refused(self):
        target = self.base / "root_link"
        target.symlink_to(self.project, target_is_directory=True)
        with self.assertRaises(ValueError):
            initialize_empty_root(target)

    def test_symlink_handoff_parent_is_refused(self):
        new_root = self.base / "another_project"
        new_root.mkdir()
        (new_root / "reference").symlink_to(self.run, target_is_directory=True)
        with self.assertRaises(ValueError):
            create_unique_handoff_run(new_root, self.run_id)

    def add_evidence(self, source_relative, payload):
        source = self.source / source_relative
        source.parent.mkdir(parents=True, exist_ok=True)
        source.write_bytes(payload)
        destination = self.run / "environment" / source.name
        destination.parent.mkdir(exist_ok=True)
        destination.write_bytes(payload)
        digest = hashlib.sha256(payload).hexdigest()
        self.manifest["copied_files"].append({
            "source_absolute_path": str(source),
            "source_relative_path": source_relative,
            "destination_relative_path": destination.relative_to(self.project).as_posix(),
            "source_sha256": digest, "destination_sha256": digest,
            "source_size_bytes": len(payload), "destination_size_bytes": len(payload),
            "copy_status": "PASS",
        })
        self.manifest["copied_file_count"] += 1
        self.manifest["copied_total_size_bytes"] += len(payload)
        self.save_configs()

    def test_exact_build_summaries_are_allowed_as_evidence(self):
        for name in ("cmake_static_safety.json", "build_execution.json"):
            self.add_evidence(
                "artifacts/phase1_v2/20261018T210029Z/build/" + name,
                b'{"status":"PASS","kind":"artificial summary"}\n')
        result = self.verify()
        self.assertTrue(result.ok, result.checks)

    def test_other_build_files_are_rejected(self):
        self.add_evidence(
            "artifacts/phase1_v2/20261018T210029Z/build/arbitrary.json",
            b'{"status":"PASS"}\n')
        self.assert_failed("only two explicitly reviewed build summaries")

    def test_elf_disguised_as_approved_summary_is_rejected(self):
        self.add_evidence(
            "artifacts/phase1_v2/20261018T210029Z/build/build_execution.json",
            bytes((127, 69, 76, 70)) + b"synthetic")
        self.assert_failed("ELF executable magic")

    def test_unquoted_credential_binding_is_rejected(self):
        name = "API_" + "KEY"
        fake = "SYNTHETIC" + "CREDENTIAL123456789"
        (self.project / "settings.txt").write_text(
            name + "=" + fake + "\n", encoding="utf-8")
        self.assert_failed("credential-like assignment")

    def test_all_policy_permission_gates_are_enforced(self):
        for key in POLICY_FALSE:
            with self.subTest(key=key):
                self.policy[key] = True
                self.save_configs()
                self.assert_failed(key)
                self.policy[key] = False

    def test_missing_experiment_security_gate_fails(self):
        del self.experiment["require_unique_run_id"]
        self.save_configs()
        self.assert_failed("require_unique_run_id")


if __name__ == "__main__":
    unittest.main()

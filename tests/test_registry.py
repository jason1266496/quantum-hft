"""Registry and base-adapter security tests using only synthetic tests/ fixtures."""

from dataclasses import FrozenInstanceError
from decimal import Decimal
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from data_pipeline.adapters.base import BaseAdapter, DataFormatError, parse_decimal, parse_integer
from data_pipeline.registry import DatasetRegistry, RegistryError, SourceValidationError
from tests.phase2a_helpers import make_registry_fixture


class RegistryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="phase2a_registry_", dir=Path(__file__).parent)
        self.addCleanup(self.temp.cleanup)
        self.config_path, self.root = make_registry_fixture(
            self.temp.name, [("example.csv", "csv", "synthetic data\n")])
        self.path = self.root / "results/example.csv"

    def registry(self, **kwargs):
        options = {"allowed_roots": (self.root,), "require_nine_sources": False}
        options.update(kwargs)
        return DatasetRegistry(self.config_path, **options)

    def alter_config(self, function):
        config = json.loads(self.config_path.read_text())
        function(config)
        self.config_path.write_text(json.dumps(config), encoding="utf-8")

    def test_normal_registry_has_frozen_metadata_and_alias(self):
        registry = self.registry()
        source = registry.get("example")
        self.assertEqual(source.access_mode, "read_only")
        self.assertEqual(source.session_id, "synthetic_example")
        self.assertEqual(source.absolute_path, str(self.path))
        self.assertEqual(registry.snapshot()["source_count"], 1)
        with self.assertRaises(FrozenInstanceError):
            source.access_mode = "write"

    def test_registry_only_opens_configuration_not_market_source(self):
        import builtins
        actual_open = builtins.open
        opened = []

        def tracked_open(path, mode="r", *args, **kwargs):
            opened.append((str(path), mode))
            self.assertEqual(Path(path), self.config_path)
            return actual_open(path, mode, *args, **kwargs)

        with patch("builtins.open", side_effect=tracked_open):
            registry = self.registry()
        self.assertEqual(len(registry.sources), 1)
        self.assertEqual(opened, [(str(self.config_path), "r")])

    def test_missing_required_source_fields(self):
        original = json.loads(self.config_path.read_text())
        for field in ("session_id", "sha256", "size_bytes", "event_time_start", "allowed_uses"):
            with self.subTest(field=field):
                mutated = json.loads(json.dumps(original))
                del mutated["sources"][0][field]
                self.config_path.write_text(json.dumps(mutated))
                with self.assertRaises(RegistryError):
                    self.registry()

    def test_missing_required_registry_field(self):
        self.alter_config(lambda config: config.pop("access_mode"))
        with self.assertRaises(RegistryError):
            self.registry()

    def test_missing_safety_metadata_rejected(self):
        original = json.loads(self.config_path.read_text())
        for field in ("allow_network", "allow_real_trading", "allow_testnet_trading", "allow_cross_session_labels",
                      "time_order_field", "local_timestamp_policy"):
            with self.subTest(field=field):
                mutated = json.loads(json.dumps(original))
                del mutated[field]
                self.config_path.write_text(json.dumps(mutated))
                with self.assertRaises(RegistryError):
                    self.registry()

    def test_incorrect_timestamp_policy_rejected(self):
        self.alter_config(lambda config: config.update(time_order_field="local_timestamp_us"))
        with self.assertRaises(RegistryError):
            self.registry()
        self.alter_config(lambda config: config.update(time_order_field="event_time_ms", local_timestamp_policy="receive_time"))
        with self.assertRaises(RegistryError):
            self.registry()

    def test_config_symlink_rejected(self):
        real_config = Path(self.temp.name) / "real_config.json"
        self.config_path.rename(real_config)
        self.config_path.symlink_to(real_config)
        with self.assertRaises(RegistryError):
            self.registry()

    def test_write_mode_rejected(self):
        for value in ("w", "read_write", "append"):
            with self.subTest(value=value):
                self.alter_config(lambda config: config.update(access_mode=value))
                with self.assertRaises(RegistryError):
                    self.registry()

    def test_per_source_write_mode_rejected(self):
        self.alter_config(lambda config: config["sources"][0].update(access_mode="write"))
        with self.assertRaises(RegistryError):
            self.registry()

    def test_enabled_writes_rejected(self):
        self.alter_config(lambda config: config.update(allow_hft_write=True))
        with self.assertRaises(RegistryError):
            self.registry()

    def test_relative_traversal_rejected_even_when_it_normalizes_inside_root(self):
        self.alter_config(lambda config: config["sources"][0].update(relative_path="results/../results/example.csv"))
        with self.assertRaises(RegistryError):
            self.registry()

    def test_absolute_traversal_rejected(self):
        self.alter_config(lambda config: config["sources"][0].update(absolute_path=str(self.root) + "/results/../results/example.csv"))
        with self.assertRaises(RegistryError):
            self.registry()

    def test_outside_source_rejected(self):
        self.alter_config(lambda config: config["sources"][0].update(absolute_path=str(Path(self.temp.name) / "outside.csv")))
        with self.assertRaises(RegistryError):
            self.registry()

    def test_root_cannot_be_changed_by_config(self):
        self.alter_config(lambda config: config.update(hft_project=str(Path(self.temp.name))))
        with self.assertRaises(RegistryError):
            self.registry()

    def test_unregistered_source_rejected(self):
        with self.assertRaises(RegistryError):
            self.registry().get("not_registered")

    def test_duplicate_source_rejected(self):
        self.alter_config(lambda config: config["sources"].append(dict(config["sources"][0])))
        with self.assertRaises(RegistryError):
            self.registry()

    def test_production_requires_nine_sources(self):
        with self.assertRaises(RegistryError):
            self.registry(require_nine_sources=True)

    def test_duplicate_csv_session_rejected(self):
        other = self.root / "results/other.csv"
        other.write_bytes(b"synthetic data\n")

        def add_other(config):
            source = dict(config["sources"][0])
            source.update(relative_path="results/other.csv", absolute_path=str(other))
            config["sources"].append(source)

        self.alter_config(add_other)
        with self.assertRaises(RegistryError):
            self.registry()

    def test_snapshot_cannot_borrow_event_time(self):
        self.alter_config(lambda config: config["sources"][0].update(file_type="snapshot"))
        with self.assertRaises(RegistryError):
            self.registry()

    def test_invalid_sha_or_size_rejected(self):
        self.alter_config(lambda config: config["sources"][0].update(sha256="invalid"))
        with self.assertRaises(RegistryError):
            self.registry()
        self.alter_config(lambda config: config["sources"][0].update(sha256="0" * 64, size_bytes=True))
        with self.assertRaises(RegistryError):
            self.registry()

    def test_symlink_outside_root_rejected(self):
        outside = Path(self.temp.name) / "outside.csv"
        outside.write_bytes(b"synthetic data\n")
        self.path.unlink()
        self.path.symlink_to(outside)
        with self.assertRaises(RegistryError):
            self.registry()

    def test_symlink_inside_root_also_rejected_conservatively(self):
        target = self.root / "results/target.csv"
        target.write_bytes(b"synthetic data\n")
        self.path.unlink()
        self.path.symlink_to(target)
        with self.assertRaises(RegistryError):
            self.registry()

    def test_symlink_parent_rejected(self):
        real_results = self.root / "real_results"
        (self.root / "results").rename(real_results)
        (self.root / "results").symlink_to(real_results, target_is_directory=True)
        with self.assertRaises(RegistryError):
            self.registry()

    def test_duplicate_json_keys_rejected(self):
        self.config_path.write_text('{"sources":[],"sources":[]}')
        with self.assertRaises(RegistryError):
            self.registry()

    def test_source_validation_and_progress(self):
        calls = []
        with BaseAdapter(self.registry(), "example") as adapter:
            result = adapter.validate_source(progress=calls.append)
        self.assertEqual(result["status"], "PASS")
        self.assertTrue(result["sha256_match"])
        self.assertEqual(calls[-1]["percent"], 100.0)
        self.assertEqual(calls[-1]["parse_errors"], 0)
        self.assertIn("eta_seconds", calls[-1])

    def test_sha_mismatch_fails_before_stream_open(self):
        self.alter_config(lambda config: config["sources"][0].update(sha256="0" * 64))
        with BaseAdapter(self.registry(), "example") as adapter:
            with self.assertRaisesRegex(SourceValidationError, "SHA-256 mismatch"):
                with adapter._open_binary():
                    self.fail("Invalid source must not be yielded")

    def test_size_mismatch_rejected(self):
        self.alter_config(lambda config: config["sources"][0].update(size_bytes=999))
        with BaseAdapter(self.registry(), "example") as adapter:
            with self.assertRaisesRegex(SourceValidationError, "size mismatch"):
                adapter.validate_source()

    def test_changed_source_invalidates_validation_cache(self):
        with BaseAdapter(self.registry(), "example") as adapter:
            adapter.validate_source()
            self.path.write_bytes(b"altered!! data\n")
            with self.assertRaises(SourceValidationError):
                adapter.validate_source()

    def test_symlink_swap_after_registration_rejected(self):
        registry = self.registry()
        outside = Path(self.temp.name) / "outside.csv"
        outside.write_bytes(b"synthetic data\n")
        self.path.unlink()
        self.path.symlink_to(outside)
        with BaseAdapter(registry, "example") as adapter:
            with self.assertRaises(SourceValidationError):
                adapter.validate_source()

    def test_adapter_open_flags_never_allow_writes(self):
        registry = self.registry()
        actual_open = os.open
        flags_seen = []

        def tracked_open(path, flags, *args, **kwargs):
            flags_seen.append(flags)
            return actual_open(path, flags, *args, **kwargs)

        before = self.path.stat()
        with patch("data_pipeline.adapters.base.os.open", side_effect=tracked_open):
            with BaseAdapter(registry, "example") as adapter:
                with adapter._open_text() as handle:
                    self.assertEqual(handle.read(), "synthetic data\n")
        after = self.path.stat()
        for flags in flags_seen:
            self.assertEqual(flags & os.O_ACCMODE, os.O_RDONLY)
            self.assertFalse(flags & (os.O_CREAT | os.O_TRUNC | os.O_APPEND))
        self.assertEqual((before.st_size, before.st_mtime_ns, before.st_ctime_ns),
                         (after.st_size, after.st_mtime_ns, after.st_ctime_ns))

    def test_close_rejects_reuse(self):
        adapter = BaseAdapter(self.registry(), "example")
        adapter.close()
        with self.assertRaisesRegex(SourceValidationError, "closed"):
            adapter.validate_source()

    def test_closed_adapter_closes_active_descriptor(self):
        adapter = BaseAdapter(self.registry(), "example")
        with adapter._open_binary() as handle:
            adapter.close()
            self.assertTrue(handle.closed)

    def test_parsers_reject_nonfinite_bool_and_unbounded_fields(self):
        kwargs = {"file": "artificial.csv", "record_index": 2, "field": "value"}
        for bad in ("NaN", "Infinity", "1_000", "1e10000", True, 1.25, "1" * 129):
            with self.subTest(value=repr(bad)):
                with self.assertRaises(DataFormatError):
                    parse_decimal(bad, **kwargs)
        for bad in ("1.0", "1e2", True, 1.5):
            with self.assertRaises(DataFormatError):
                parse_integer(bad, **kwargs)
        self.assertEqual(parse_integer("123", **kwargs), 123)
        self.assertEqual(parse_decimal("0.125", **kwargs), Decimal("0.125"))


if __name__ == "__main__":
    unittest.main()

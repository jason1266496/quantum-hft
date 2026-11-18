"""Feature output tests use only artificial rows under Phase 2C fixtures."""

import csv
import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from decimal import Decimal, localcontext

from data_pipeline.features.schema import fields
from data_pipeline.features.writer import FeatureWriter, PROJECT_ROOT, write_json, json_safe

FIXTURES = PROJECT_ROOT / "tests" / "fixtures" / "phase2c"


def row(view="aggregate_core_v1", index=1):
    data = {name: Decimal("1") for name in fields(view)}
    data.update(schema_version="1.0", feature_view=view, source_id="fixture",
                session_id="session", record_index=index, event_time_ms=1000 + index,
                first_update_id=None, final_update_id=None, local_update_id=None,
                valid_feature_row=True, invalid_reason="")
    return data


class FeatureWriterTests(unittest.TestCase):
    def setUp(self):
        FIXTURES.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(prefix="writer_", dir=FIXTURES)
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.output = self.root / "artifacts" / "phase2c" / "artificial"
        self.output.mkdir(parents=True)

    def writer(self, name="features.csv", view="aggregate_core_v1"):
        return FeatureWriter(self.output / name, view, project_root=self.root)

    def test_fixed_column_order_independent_of_mapping_order(self):
        data = row()
        with self.writer() as writer:
            writer.write(dict(reversed(list(data.items()))))
        with (self.output / "features.csv").open(newline="") as handle:
            records = list(csv.reader(handle))
        self.assertEqual(records[0], list(fields("aggregate_core_v1")))
        self.assertEqual(records[1][records[0].index("source_id")], "fixture")

    def test_canonical_decimal_no_scientific_notation(self):
        data = row()
        data.update(best_bid=Decimal("1.23000"), best_ask=Decimal("1E+5"),
                    obi_5=Decimal("-0.0000"))
        writer = self.writer()
        writer.write(data)
        writer.close()
        with (self.output / "features.csv").open(newline="") as handle:
            rows = list(csv.DictReader(handle))
        self.assertEqual(rows[0]["best_bid"], "1.23")
        self.assertEqual(rows[0]["best_ask"], "100000")
        self.assertEqual(rows[0]["obi_5"], "0")

    def test_utf8_lf_and_csv_quoting(self):
        data = row()
        data["source_id"] = '人工,來源"一"'
        with self.writer() as writer:
            writer.write(data)
        content = (self.output / "features.csv").read_bytes()
        self.assertNotIn(b"\r", content)
        self.assertTrue(content.endswith(b"\n"))
        decoded = next(csv.DictReader(io.StringIO(content.decode("utf-8"))))
        self.assertEqual(decoded["source_id"], data["source_id"])

    def test_null_and_boolean_encoding(self):
        with self.writer() as writer:
            writer.write(row())
            data = row(index=2)
            data.update(valid_feature_row=False, invalid_reason="TEST_INVALID", obi_5=None)
            writer.write(data)
        with (self.output / "features.csv").open(newline="") as handle:
            records = list(csv.DictReader(handle))
        self.assertEqual(records[0]["first_update_id"], "")
        self.assertEqual(records[0]["valid_feature_row"], "true")
        self.assertEqual(records[1]["valid_feature_row"], "false")
        self.assertEqual(records[1]["obi_5"], "")

    def test_invalid_row_is_retained(self):
        data = row()
        data.update(valid_feature_row=False, invalid_reason="INSUFFICIENT_TOP5_DEPTH")
        writer = self.writer()
        writer.write(data)
        self.assertEqual(writer.close()["row_count"], 1)

    def test_existing_output_is_not_overwritten(self):
        writer = self.writer()
        writer.write(row())
        writer.close()
        before = (self.output / "features.csv").read_bytes()
        with self.assertRaises(FileExistsError):
            self.writer()
        self.assertEqual((self.output / "features.csv").read_bytes(), before)

    def test_exact_schema_rejects_extra_label_target_local_timestamp(self):
        for field in ("label", "target", "future_return", "local_timestamp_us"):
            with self.subTest(field=field):
                with self.writer(field + ".csv") as writer:
                    data = row()
                    data[field] = 3
                    with self.assertRaises(ValueError):
                        writer.write(data)
                    self.assertEqual(writer.row_count, 0)

    def test_missing_schema_column_rejected(self):
        with self.writer() as writer:
            data = row()
            data.pop("obi_5")
            with self.assertRaises(ValueError):
                writer.write(data)

    def test_mixed_view_rejected(self):
        with self.writer() as writer:
            with self.assertRaises(ValueError):
                writer.write(row("depth_top5_v1"))

    def test_wrong_view_value_rejected(self):
        with self.writer() as writer:
            data = row()
            data["feature_view"] = "depth_top5_v1"
            with self.assertRaises(ValueError):
                writer.write(data)

    def test_cross_source_rejected(self):
        with self.writer() as writer:
            writer.write(row())
            data = row(index=2)
            data["source_id"] = "another"
            with self.assertRaises(ValueError):
                writer.write(data)
            self.assertEqual(writer.row_count, 1)

    def test_cross_session_rejected(self):
        with self.writer() as writer:
            writer.write(row())
            data = row(index=2)
            data["session_id"] = "another"
            with self.assertRaises(ValueError):
                writer.write(data)

    def test_float_and_nonfinite_rejected(self):
        for index, value in enumerate((1.2, Decimal("NaN"), Decimal("sNaN"), Decimal("Infinity"))):
            with self.writer(str(index) + ".csv") as writer:
                data = row()
                data["mid_price"] = value
                with self.assertRaises(ValueError):
                    writer.write(data)

    def test_bool_rejected_as_integer_or_decimal(self):
        for field in ("event_time_ms", "mid_price"):
            with self.writer(field + ".csv") as writer:
                data = row()
                data[field] = True
                with self.assertRaises(ValueError):
                    writer.write(data)

    def test_negative_integer_rejected(self):
        with self.writer() as writer:
            data = row()
            data["record_index"] = -1
            with self.assertRaises(ValueError):
                writer.write(data)

    def test_valid_flag_requires_boolean(self):
        with self.writer() as writer:
            data = row()
            data["valid_feature_row"] = 1
            with self.assertRaises(ValueError):
                writer.write(data)

    def test_hash_and_size_match_actual_bytes(self):
        writer = self.writer()
        writer.write(row())
        metadata = writer.close()
        content = (self.output / "features.csv").read_bytes()
        self.assertEqual(metadata["sha256"], hashlib.sha256(content).hexdigest())
        self.assertEqual(metadata["size_bytes"], len(content))
        self.assertEqual(metadata["row_count"], 1)
        self.assertEqual(metadata["schema_hash"], metadata["feature_schema_hash"])

    def test_same_rows_have_identical_hashes(self):
        a, b = self.writer("a.csv"), self.writer("b.csv")
        for index in range(1, 4):
            a.write(row(index=index))
            b.write(dict(reversed(list(row(index=index).items()))))
        self.assertEqual(a.close(), b.close())

    def test_decimal_output_independent_of_ambient_context(self):
        data = row()
        data["best_bid"] = Decimal("123456789012345678901234567890.000001")
        a, b = self.writer("a.csv"), self.writer("b.csv")
        a.write(data)
        with localcontext() as ctx:
            ctx.prec = 4
            b.write(data)
        self.assertEqual(a.close()["sha256"], b.close()["sha256"])

    def test_progress_messages_do_not_affect_output(self):
        a, b = self.writer("a.csv"), self.writer("b.csv")
        progress = io.StringIO()
        for index in range(1, 4):
            a.write(row(index=index))
            print("progress", index, file=progress)
            b.write(row(index=index))
        self.assertEqual(a.close()["sha256"], b.close()["sha256"])

    def test_close_is_idempotent_and_later_write_rejected(self):
        writer = self.writer()
        writer.write(row())
        first = writer.close()
        self.assertEqual(writer.close(), first)
        with self.assertRaises(ValueError):
            writer.write(row(index=2))

    def test_hft_output_rejected_without_open(self):
        for target in ("/home/jason/hft-realtime/x.csv",
                       "/home/jason/hft-realtime-codex/results/x.csv",
                       "/home/jason/hft-realtime-codex-incomplete-20261018T194544Z/x.csv"):
            with self.assertRaises(ValueError):
                FeatureWriter(target, "aggregate_core_v1")

    def test_output_escape_and_missing_parent_rejected(self):
        with self.assertRaises(ValueError):
            FeatureWriter(self.root / "escape.csv", "aggregate_core_v1", project_root=self.root)
        with self.assertRaises(ValueError):
            self.writer("missing/child.csv")

    def test_project_root_cannot_escape_quantum(self):
        with self.assertRaises(ValueError):
            FeatureWriter("/tmp/artifacts/phase2c/test.csv", "aggregate_core_v1",
                          project_root="/tmp")

    def test_symlink_parent_and_target_rejected(self):
        link = self.output / "link"
        link.symlink_to(self.output, target_is_directory=True)
        with self.assertRaises(ValueError):
            self.writer("link/test.csv")
        target = self.output / "existing.csv"
        target.write_text("artificial", encoding="utf-8")
        pointer = self.output / "pointer.csv"
        pointer.symlink_to(target)
        with self.assertRaises(ValueError):
            self.writer("pointer.csv")

    def test_json_sorted_keys_decimal_utf8_lf(self):
        path = self.output / "quality.json"
        metadata = write_json(path, {"z": Decimal("1.23000"), "a": "測試"}, project_root=self.root)
        content = path.read_bytes()
        self.assertEqual(json.loads(content), {"a": "測試", "z": "1.23"})
        self.assertLess(content.index(b'"a"'), content.index(b'"z"'))
        self.assertNotIn(b"\r", content)
        self.assertTrue(content.endswith(b"\n"))
        self.assertEqual(metadata["sha256"], hashlib.sha256(content).hexdigest())

    def test_json_output_existing_rejected(self):
        path = self.output / "quality.json"
        write_json(path, {"a": 1}, project_root=self.root)
        with self.assertRaises(FileExistsError):
            write_json(path, {"a": 2}, project_root=self.root)

    def test_json_float_nonfinite_and_nonstring_keys_rejected(self):
        for value in ({"a": 1.2}, {"a": Decimal("NaN")}, {1: "a"}):
            with self.assertRaises(ValueError):
                json_safe(value)


if __name__ == "__main__":
    unittest.main()


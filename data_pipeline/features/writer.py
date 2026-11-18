"""Exclusive, fixed-schema feature serialization with project-scoped outputs."""

from __future__ import annotations

import csv
import hashlib
import json
from decimal import Decimal
from pathlib import Path

from data_pipeline.orderbook.canonical import canonical_decimal
from .schema import fields, schema_hash

PROJECT_ROOT = Path(__file__).resolve().parents[2]
FORBIDDEN_ROOTS = (
    Path("/home/jason/hft-realtime"),
    Path("/home/jason/hft-realtime-codex"),
    Path("/home/jason/hft-realtime-codex-incomplete-20261018T194544Z"),
)
STRING_FIELDS = {"schema_version", "feature_view", "source_id", "session_id", "invalid_reason"}
INTEGER_FIELDS = {"record_index", "event_time_ms", "first_update_id", "final_update_id", "local_update_id"}


def _inside(path, parent):
    return path == parent or parent in path.parents


def safe_output_path(path, *, project_root=None):
    """Reject links, HFT locations, and every path outside approved new outputs."""
    root = Path(project_root) if project_root is not None else PROJECT_ROOT
    root = root.absolute()
    target = Path(path)
    if not target.is_absolute():
        target = root / target
    target = target.absolute()
    for value in (root, target):
        for part in (value, *value.parents):
            if part.is_symlink():
                raise ValueError("SYMLINK_OUTPUT_PROHIBITED")
    root = root.resolve()
    target = target.resolve()
    if not _inside(root, PROJECT_ROOT.resolve()):
        raise ValueError("PROJECT_ROOT_OUTSIDE_QUANTUM_PROJECT")
    if any(_inside(target, forbidden) or _inside(root, forbidden) for forbidden in FORBIDDEN_ROOTS):
        raise ValueError("HFT_OUTPUT_PROHIBITED")
    allowed = (root / "artifacts" / "phase2c", root / "tests" / "fixtures" / "phase2c")
    if not any(_inside(target, parent) and target != parent for parent in allowed):
        raise ValueError("OUTPUT_OUTSIDE_PHASE2C")
    if not target.parent.is_dir():
        raise ValueError("OUTPUT_PARENT_MUST_EXIST")
    if target.exists():
        raise FileExistsError(str(target))
    return target


def json_safe(value):
    """Convert Decimal values without accepting nonfinite numbers or floats."""
    if isinstance(value, Decimal):
        return canonical_decimal(value)
    if type(value) is float:
        raise ValueError("FLOAT_OUTPUT_PROHIBITED")
    if value is None or type(value) in (str, int, bool):
        return value
    if isinstance(value, dict):
        if any(type(key) is not str for key in value):
            raise ValueError("JSON_KEYS_MUST_BE_STRINGS")
        return {key: json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_safe(item) for item in value]
    raise TypeError("UNSUPPORTED_JSON_VALUE")


def write_json(path, value, *, project_root=None):
    """Write one UTF-8/LF sorted-key JSON document, exclusively."""
    target = safe_output_path(path, project_root=project_root)
    encoded = (json.dumps(json_safe(value), sort_keys=True, ensure_ascii=False,
                          allow_nan=False, indent=2) + "\n").encode("utf-8")
    with target.open("xb") as handle:
        handle.write(encoded)
    return {"sha256": hashlib.sha256(encoded).hexdigest(), "size_bytes": len(encoded)}


class FeatureWriter:
    """One source/session/view per file. Caller must create a new run directory."""

    def __init__(self, path, view, *, project_root=None):
        self.view = view
        self.column_order = tuple(fields(view))
        self.path = safe_output_path(path, project_root=project_root)
        self._schema_hash = schema_hash(view)
        self._handle = self.path.open("x", encoding="utf-8", newline="")
        self._writer = csv.writer(self._handle, lineterminator="\n")
        self._writer.writerow(self.column_order)
        self._identity = None
        self.row_count = 0
        self._result = None

    def write(self, row):
        if self._result is not None:
            raise ValueError("WRITER_CLOSED")
        if not isinstance(row, dict) or set(row) != set(self.column_order):
            raise ValueError("FEATURE_FIELDS_MUST_EXACTLY_MATCH_SCHEMA")
        if row.get("feature_view") != self.view:
            raise ValueError("FEATURE_VIEW_MISMATCH")
        identity = (row.get("source_id"), row.get("session_id"))
        if any(type(value) is not str or not value for value in identity):
            raise ValueError("INVALID_SOURCE_IDENTITY")
        if self._identity is not None and identity != self._identity:
            raise ValueError("CROSS_SOURCE_OR_SESSION_OUTPUT_PROHIBITED")
        values = []
        for name in self.column_order:
            value = row[name]
            if value is None:
                values.append("")
            elif name in STRING_FIELDS:
                if type(value) is not str:
                    raise ValueError("INVALID_STRING_FIELD: " + name)
                values.append(value)
            elif name in INTEGER_FIELDS:
                if type(value) is not int or value < 0:
                    raise ValueError("INVALID_INTEGER_FIELD: " + name)
                values.append(str(value))
            elif name == "valid_feature_row":
                if type(value) is not bool:
                    raise ValueError("INVALID_VALIDITY_FLAG")
                values.append("true" if value else "false")
            else:
                if type(value) is not Decimal or not value.is_finite():
                    raise ValueError("FINITE_DECIMAL_REQUIRED: " + name)
                values.append(canonical_decimal(value))
        self._writer.writerow(values)
        self._identity = identity
        self.row_count += 1

    def close(self):
        if self._result is None:
            self._handle.close()
            digest = hashlib.sha256()
            size = 0
            with self.path.open("rb") as handle:
                for block in iter(lambda: handle.read(1024 * 1024), b""):
                    digest.update(block)
                    size += len(block)
            self._result = {
                "row_count": self.row_count,
                "column_order": list(self.column_order),
                "schema_hash": self._schema_hash,
                "feature_schema_hash": self._schema_hash,
                "sha256": digest.hexdigest(),
                "size_bytes": size,
            }
        return dict(self._result)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()
        return False


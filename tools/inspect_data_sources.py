"""Phase 2A metadata/hash and bounded-schema inspection; no model or book building."""
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import sys
import time

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from data_pipeline.registry import DatasetRegistry, RegistryError, SourceValidationError
from data_pipeline.adapters.base import DataFormatError
from data_pipeline.adapters.csv_adapter import CSVAdapter
from data_pipeline.adapters.snapshot_adapter import SnapshotAdapter
from data_pipeline.adapters.replay_adapter import ReplayAdapter

ADAPTERS = {"csv": CSVAdapter, "snapshot": SnapshotAdapter, "replay": ReplayAdapter}
RUN_PATTERN = re.compile(r"[0-9]{8}T[0-9]{6}Z\Z")
POLICY_FALSE = (
    "cross_session_labels", "cross_file_labels", "local_timestamp_is_receive_time",
    "local_timestamp_allowed_as_feature", "local_timestamp_allowed_for_network_latency",
    "local_timestamp_allowed_for_tick_to_trade", "allow_final_holdout_for_selection",
)
POLICY_TRUE = (
    "session_isolation", "record_actual_horizon", "record_match_error",
    "invalidate_on_large_gap", "invalidate_session_tail", "require_clock_source_metadata",
)
LABEL_FIELDS = {
    "requested_horizon_ms", "actual_horizon_ms", "target_event_time_ms",
    "match_error_ms", "valid_label", "invalid_reason",
}


def _no_symlink(path):
    for item in (path, *path.parents):
        if item.is_symlink():
            raise ValueError(f"symbolic link is forbidden: {item}")


def _absolute(path, root):
    raw = os.fspath(path)
    if "\\" in raw or "\x00" in raw or ".." in raw.split("/"):
        raise ValueError("unsafe path components")
    result = Path(raw) if os.path.isabs(raw) else root / raw
    _no_symlink(result)
    return result


def _policy(path):
    _no_symlink(path)
    with os.fdopen(os.open(path, os.O_RDONLY | os.O_NOFOLLOW | getattr(os, "O_NOATIME", 0)),
                   "r", encoding="utf-8") as handle:
        policy = json.load(handle)
    if not isinstance(policy, dict):
        raise ValueError("timestamp policy must be an object")
    if policy.get("ordering_field") != "event_time_ms":
        raise ValueError("event_time_ms is the only ordering field")
    for key in POLICY_FALSE:
        if policy.get(key) is not False:
            raise ValueError(f"timestamp policy {key} must be false")
    for key in POLICY_TRUE:
        if policy.get(key) is not True:
            raise ValueError(f"timestamp policy {key} must be true")
    if policy.get("horizons_ms") != [100, 200, 500, 1000]:
        raise ValueError("timestamp horizons differ from the approved policy")
    label_fields = policy.get("required_label_fields")
    if (not isinstance(label_fields, list)
            or not all(isinstance(field, str) for field in label_fields)
            or not LABEL_FIELDS <= set(label_fields)):
        raise ValueError("required label provenance fields are missing")
    if "max_match_error_ms" not in policy or policy["max_match_error_ms"] is not None:
        raise ValueError("max_match_error_ms must remain null in Phase 2A")
    if policy.get("selection_status") != "TO_BE_DETERMINED_FROM_TRAINING_DATA_PROFILE_AND_RESEARCH_PROTOCOL":
        raise ValueError("unapproved match-error selection policy")
    return policy


def _output_path(value, project_root):
    path = _absolute(value, project_root)
    if path.parent != project_root / "artifacts" / "phase2a":
        raise ValueError("output must be artifacts/phase2a/<UTC_run_id>")
    if not RUN_PATTERN.fullmatch(path.name):
        raise ValueError("invalid UTC run_id format")
    datetime.strptime(path.name, "%Y%m%dT%H%M%SZ")
    report = project_root / "docs" / f"PHASE2A_REPORT_{path.name}.md"
    if os.path.lexists(path) or os.path.lexists(report):
        raise FileExistsError("output run or formal report already exists; refusing overwrite")
    _no_symlink(path.parent)
    return path


def _write_json(path, value):
    with open(path, "x", encoding="utf-8", newline="\n") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2, allow_nan=False)
        handle.write("\n")


def inspect_sources(config_path, output_path, *, sample_records=100, full_scan=False,
                    project_root=PROJECT_ROOT, allowed_roots=None,
                    require_nine_sources=True, timestamp_policy_path=None,
                    progress_stream=None, command=None):
    """Only metadata, streamed SHA, and schema inspection. Never persist raw records.

    Explicit alternate roots are only for artificial unittest fixtures. CLI uses
    fixed project and registered HFT roots. A full SHA requires every byte, even
    when full_scan is false; full_scan controls record-level parsing, not hashing.
    """
    if type(sample_records) is not int or sample_records <= 0:
        raise ValueError("sample_records must be a positive integer")
    if type(full_scan) is not bool:
        raise ValueError("full_scan must be boolean")
    root = Path(project_root).absolute()
    _no_symlink(root)
    config = _absolute(config_path, root)
    if not config.is_relative_to(root):
        raise ValueError("config must be inside this project")
    policy_path = _absolute(timestamp_policy_path or root / "configs/timestamp_policy.json", root)
    if not policy_path.is_relative_to(root):
        raise ValueError("timestamp policy must be inside this project")
    output = _output_path(output_path, root)
    registry = DatasetRegistry(config, allowed_roots=allowed_roots,
                               require_nine_sources=require_nine_sources)
    policy = _policy(policy_path)
    # Metadata-only registry and policy must pass before creating any run.
    output.parent.mkdir(parents=True, exist_ok=True)
    output.mkdir()
    started_at = datetime.now(timezone.utc).isoformat()
    start = time.monotonic()
    stream = progress_stream if progress_stream is not None else sys.stdout
    sources = tuple(registry.sources)
    rows = []
    summaries = []
    completed = 0
    errors = 0
    total_bytes = sum(source.expected_size_bytes for source in sources)
    completed_bytes = 0
    last_progress = -10.0

    def emit(source=None, payload=None, force=False):
        nonlocal last_progress
        elapsed = time.monotonic() - start
        if not force and elapsed - last_progress < 1.0:
            return
        last_progress = elapsed
        progress_bytes = int((payload or {}).get("processed_bytes", 0))
        done = min(total_bytes, completed_bytes + progress_bytes)
        percent = 100.0 * done / total_bytes if total_bytes else 100.0
        eta = elapsed * (total_bytes - done) / done if done else None
        value = {
            "stage": "hash_and_bounded_schema" if not full_scan else "hash_and_full_schema",
            "source_id": source.source_id if source is not None else None,
            "processed_files": completed, "total_files": len(sources),
            "processed_bytes": done, "total_bytes": total_bytes,
            "percent": round(percent, 3), "elapsed_seconds": round(elapsed, 6),
            "eta_seconds": round(eta, 6) if eta is not None else "NOT_AVAILABLE",
            "parse_errors": errors,
        }
        print(json.dumps(value, ensure_ascii=False), file=stream, flush=True)

    emit(force=True)
    failures = []
    for source in sources:
        row = {
            "source_id": source.source_id, "session_id": source.session_id,
            "relative_path": source.relative_path, "absolute_path": source.absolute_path,
            "file_type": source.file_type, "access_mode": source.access_mode,
            "audit_status": source.audit_status,
            "expected_sha256": source.expected_sha256,
            "expected_size_bytes": source.expected_size_bytes,
            "actual_sha256": None, "actual_size_bytes": None,
            "metadata_status": "NOT_AVAILABLE", "sha256_status": "NOT_AVAILABLE",
            "size_status": "NOT_AVAILABLE", "close_status": "NOT_AVAILABLE",
            "schema_status": "NOT_AVAILABLE", "status": "NOT_AVAILABLE",
            "schema_variant": "NOT_AVAILABLE",
            "checked_records": 0, "parse_errors": 0, "error": None,
            "error_details": None, "errors": [],
        }
        adapter = None
        summary = None
        phase = "adapter_initialization"

        def record_failure(exc, failure_phase):
            nonlocal errors
            details = {
                "source_id": source.source_id, "phase": failure_phase,
                "exception_type": type(exc).__name__,
                "file": getattr(exc, "file", source.absolute_path),
                "record_index": getattr(exc, "record_index", None),
                "physical_line": getattr(exc, "physical_line", None),
                "side": getattr(exc, "side", "NOT_AVAILABLE"),
                "update_index": getattr(exc, "update_index", "NOT_AVAILABLE"),
                "safe_summary": getattr(exc, "safe_summary", None),
            }
            entry = {"source_id": source.source_id, "error": str(exc),
                     "error_details": details}
            row["status"] = "FAIL"
            if row["error"] is None:
                row["error"] = str(exc)
                row["error_details"] = details
            row["errors"].append(entry)
            failures.append(entry)
            parse_error = isinstance(exc, (DataFormatError, UnicodeError,
                                          json.JSONDecodeError, csv.Error))
            row["parse_errors"] += int(parse_error)
            errors += int(parse_error)
            if failure_phase == "source_validation":
                # The exception does not provide the actual hash/size. Do not
                # infer a size mismatch from a SHA failure, or vice versa.
                row["metadata_status"] = "FAIL"
            elif failure_phase == "schema":
                row["schema_status"] = "FAIL"
            elif failure_phase == "close":
                row["close_status"] = "FAIL"

        try:
            adapter = ADAPTERS[source.file_type](registry, source.source_id)
            phase = "source_validation"
            validation = adapter.validate_source(
                progress=lambda payload: emit(source, payload))
            row.update({
                "actual_sha256": validation["actual_sha256"],
                "actual_size_bytes": validation["actual_size_bytes"],
                "metadata_status": "PASS", "sha256_status": "PASS",
                "size_status": "PASS",
            })
            phase = "schema"
            summary = adapter.inspect_schema(
                sample_records=None if full_scan else sample_records)
            if not isinstance(summary, dict) or summary.get("status") != "PASS":
                raise ValueError("adapter did not return a PASS schema summary")
            row.update({
                "schema_status": "PASS", "status": "PASS",
                "checked_records": summary.get("checked_records", summary.get("records_checked", 0)),
                "parse_errors": summary.get("parse_errors", 0),
                "schema_scope": summary.get("schema_scope", "BOUNDED_SAMPLE" if not full_scan else "FULL_SCAN"),
                "schema_variant": summary.get("schema_variant", "NOT_AVAILABLE"),
            })
        except Exception as exc:
            # Isolate each source, including constructor/programming failures.
            # KeyboardInterrupt/SystemExit still propagate to the operator.
            record_failure(exc, phase)
        finally:
            if adapter is not None:
                try:
                    adapter.close()
                    row["close_status"] = "PASS"
                except Exception as exc:
                    record_failure(exc, "close")
        summaries.append({
            "source_id": source.source_id, "session_id": source.session_id,
            "file_type": source.file_type,
            "summary": summary if row["status"] == "PASS" else {
                "status": "FAIL", "error": row["error"],
                "error_details": row["error_details"], "errors": row["errors"],
                "schema_summary": summary,
            },
        })
        rows.append(row)
        completed += 1
        completed_bytes += source.expected_size_bytes
        emit(source, force=True)
    success = not failures and all(row["status"] == "PASS" for row in rows)
    elapsed = time.monotonic() - start
    snapshot = registry.snapshot()
    snapshot.update({
        "run_id": output.name, "created_at_utc": started_at,
        "session_isolation": True, "cross_file_merge_performed": False,
        "registry_market_files_opened": False,
    })
    result = {
        "schema_version": "1.0", "run_id": output.name,
        "status": "PASS" if success else "FAIL",
        "started_at_utc": started_at,
        "completed_at_utc": datetime.now(timezone.utc).isoformat(),
        "elapsed_seconds": elapsed, "source_count": len(sources),
        "sources_passed": sum(row["status"] == "PASS" for row in rows),
        "sources_attempted": len(rows),
        "sources_checked": sum(row["metadata_status"] != "NOT_AVAILABLE" for row in rows),
        "sources_schema_checked": sum(row["schema_status"] != "NOT_AVAILABLE" for row in rows),
        "sources_failed": sum(row["status"] == "FAIL" for row in rows),
        "parse_errors": errors, "sample_records": sample_records,
        "full_scan": full_scan,
        "hash_scope": "FULL_FILE_BYTES_STREAMED_REQUIRED_FOR_SHA256",
        "schema_scope": "ALL_RECORDS" if full_scan else "BOUNDED_RECORD_VALUES; SNAPSHOT_STRUCTURE_STREAMED",
        "session_isolation": True, "cross_file_merge_performed": False,
        "timestamp_policy": {
            "ordering_field": policy["ordering_field"],
            "local_timestamp_is_receive_time": False,
            "local_timestamp_allowed_as_feature": False,
            "local_timestamp_allowed_for_network_latency": False,
            "local_timestamp_allowed_for_tick_to_trade": False,
            "max_match_error_ms": None,
            "labels_created": False,
        },
        "hft_write_performed": False, "raw_market_data_copied": False,
        "network_activity_performed": False, "model_created": False,
        "book_rebuilding_performed": False, "rows": rows,
        "warnings": [
            "Existing CSV audit WARNING remains; local timestamp is not verified receive time.",
            "Bounded inspection does not establish schema/value validity of unsampled CSV/Replay rows."
            if not full_scan else "Full schema inspection does not establish exchange truth or Book reconstruction correctness.",
            "Snapshot event timestamps and historical collector session identities remain NOT_AVAILABLE.",
        ],
        "failure": failures[0]["error"] if failures else None,
        "failures": failures,
    }
    _write_json(output / "registry_snapshot.json", snapshot)
    _write_json(output / "source_validation.json", result)
    with open(output / "source_validation.csv", "x", encoding="utf-8", newline="") as handle:
        fields = [
            "source_id", "session_id", "relative_path", "file_type", "audit_status",
            "expected_sha256", "actual_sha256", "expected_size_bytes", "actual_size_bytes",
            "metadata_status", "sha256_status", "size_status", "schema_status",
            "schema_variant", "close_status", "status", "checked_records",
            "parse_errors", "error",
        ]
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    _write_json(output / "adapter_summary.json", {
        "run_id": output.name, "status": result["status"], "full_scan": full_scan,
        "sample_records": sample_records, "adapters": summaries,
        "raw_records_saved": False, "book_rebuilt": False, "features_created": False,
        "labels_created": False,
    })
    invocation = command or {
        "api": "inspect_sources", "config": str(config), "output": str(output),
        "sample_records": sample_records, "full_scan": full_scan,
    }
    with open(output / "command_history.txt", "x", encoding="utf-8") as handle:
        handle.write(json.dumps({
            "command": invocation, "cwd": os.getcwd(), "run_id": output.name,
            "completed_at_utc": result["completed_at_utc"],
            "exit_code": 0 if success else 1,
            "notes": "完整主代理/子代理開發命令與前置驗證另存本run的ledgers；此工具不改寫既有history。",
        }, ensure_ascii=False, indent=2) + "\n")
    print(f"SOURCE INSPECTION {result['status']}; sources={result['sources_passed']}/{len(sources)}; parse_errors={errors}",
          file=stream, flush=True)
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--sample-records", type=int, default=100)
    parser.add_argument("--full-scan", action="store_true")
    args = parser.parse_args(argv)
    if Path.cwd() != PROJECT_ROOT or str(PROJECT_ROOT) != "/home/jason/quantum-hft":
        print("SOURCE INSPECTION FAIL: wrong working/project directory", file=sys.stderr)
        return 1
    try:
        result = inspect_sources(
            args.config, args.output, sample_records=args.sample_records,
            full_scan=args.full_scan,
            command=["python3", "tools/inspect_data_sources.py", *(argv if argv is not None else sys.argv[1:])],
        )
    except (ValueError, OSError, RegistryError, SourceValidationError) as error:
        print(f"SOURCE INSPECTION FAIL: {error}", file=sys.stderr)
        return 1
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())

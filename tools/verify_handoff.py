"""Read-only verification of a Phase 1 research handoff, using only stdlib.

CLI roots are fixed. The Python API accepts explicit expected roots solely so
unit tests can use artificial fixtures beneath tests/, without reading HFT data.
The nine data-source records are validated as metadata; market files are never
opened. Evidence copies are the only files read from the HFT source project.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat

SOURCE_PROJECT = Path("/home/jason/hft-realtime-codex")
DESTINATION_PROJECT = Path("/home/jason/quantum-hft")
RUN_IDS = {
    "phase1_v2_run_id": "20261018T210029Z",
    "timestamp_review_run_id": "20261018T212122Z",
    "recovery_run_id": "20261018T202030Z",
}
MARKET_NAMES = frozenset({
    "obi_market_data_20260827_session1.csv",
    "obi_market_data_20260827_session2.csv",
    "obi_market_data_20260827_session3.csv",
    "obi_market_data_test_20260827.csv",
    "obi_market_data.csv",
    "replay_snapshot_1000.json",
    "replay_events_1000.jsonl",
    "replay_snapshot_50000.json",
    "replay_events_50000.jsonl",
})
COPY_FIELDS = (
    "source_absolute_path", "source_relative_path", "destination_relative_path",
    "source_sha256", "destination_sha256", "source_size_bytes",
    "destination_size_bytes", "copy_status",
)
MANIFEST_FIELDS = (
    "schema_version", "handoff_run_id", "created_at_utc", "source_project",
    "destination_project", "phase1_v2_run_id", "timestamp_review_run_id",
    "recovery_run_id", "phase1_v2_status", "timestamp_review_status",
    "phase2_decision", "copied_files", "missing_files", "excluded_paths",
    "read_only_input_paths", "copied_file_count", "copied_total_size_bytes",
    "all_hashes_match", "hft_source_modified", "network_activity_performed",
    "trading_activity_performed", "model_training_performed",
)
SOURCE_FIELDS = (
    "relative_path", "absolute_path", "file_type", "sha256", "size_bytes",
    "audit_status", "session_id", "event_time_start", "event_time_end",
    "allowed_uses", "prohibited_uses", "known_limitations",
)
POLICY_FALSE = (
    "cross_session_labels", "local_timestamp_is_receive_time",
    "local_timestamp_allowed_as_feature",
    "local_timestamp_allowed_for_network_latency",
    "cross_file_labels", "local_timestamp_allowed_for_tick_to_trade",
    "allow_final_holdout_for_selection",
)
POLICY_TRUE = (
    "session_isolation", "record_actual_horizon", "record_match_error",
    "invalidate_on_large_gap", "invalidate_session_tail",
    "require_clock_source_metadata",
)
REQUIRED_LABEL_FIELDS = {
    "requested_horizon_ms", "actual_horizon_ms", "target_event_time_ms",
    "match_error_ms", "valid_label", "invalid_reason",
}
EXPERIMENT_FALSE = (
    "allow_network", "allow_hft_write", "allow_real_trading",
    "allow_testnet_trading", "allow_model_training", "allow_backtesting",
    "allow_paper_trading", "allow_phase2_execution", "overwrite_existing_outputs",
    "shuffle_before_split", "final_holdout_for_search",
)
EXPERIMENT_TRUE = (
    "require_human_approval", "require_unique_run_id", "record_source_sha256",
    "record_code_version", "record_parameters", "record_environment",
    "time_split_only", "purge_overlapping_labels",
)
BUILD_SUMMARY_SOURCES = frozenset({
    "artifacts/phase1_v2/20261018T210029Z/build/cmake_static_safety.json",
    "artifacts/phase1_v2/20261018T210029Z/build/build_execution.json",
})
SELECTION_STATUS = (
    "TO_BE_DETERMINED_FROM_TRAINING_DATA_PROFILE_AND_RESEARCH_PROTOCOL"
)
HEX256 = re.compile(r"[0-9a-f]{64}\Z")
RUN_ID_RE = re.compile(r"[0-9]{8}T[0-9]{6}Z\Z")
PRIVATE_BLOCK = re.compile(
    rb"(?m)^-----BEGIN (?:[A-Z0-9]+ )*(?:PRIVATE KEY|CERTIFICATE)-----\s*$"
)
# A mention of API Key, or an environment-variable name, is not a credential.
# Only a quoted literal assigned to a credential-like key is examined.
CREDENTIAL_BINDING = re.compile(
    r"""(?im)(?<![A-Za-z0-9_])["']?"""
    r"""(?:binance[_-]?)?(?:api[_-]?key|secret[_-]?key|api[_-]?secret|"""
    r"""access[_-]?token|client[_-]?secret)["']?\s*[:=]\s*"""
    r"""["']([^"'\r\n]+)["']"""
)
UNQUOTED_CREDENTIAL_BINDING = re.compile(
    r"(?im)^\s*(?:export\s+)?(?:binance[_-]?)?"
    r"(?:api[_-]?key|secret[_-]?key|api[_-]?secret|access[_-]?token|client[_-]?secret)"
    r"\s*=\s*([A-Za-z0-9_+/=-]+)\s*(?:#.*)?$"
)
PLACEHOLDER = re.compile(
    r"(?i)^(?:none|null|false|not_available|unknown|redacted|placeholder|"
    r"your[_ -].*|example[_ -].*|dummy[_ -].*|test[_ -].*|"
    r"changeme|insert[_ -].*|replace[_ -].*|<[^>]+>|\$\{[^}]+\})$"
)
MAX_EVIDENCE_BYTES = 64 * 1024 * 1024


@dataclass
class VerificationResult:
    checks: list[dict] = field(default_factory=list)

    def add(self, status, check, detail):
        self.checks.append({"status": status, "check": check, "detail": str(detail)})

    @property
    def failures(self):
        return [item for item in self.checks if item["status"] == "FAIL"]

    @property
    def warnings(self):
        return [item for item in self.checks if item["status"] == "WARNING"]

    @property
    def ok(self):
        return not self.failures

    @property
    def status(self):
        # A successful handoff check preserves inherited research warnings.
        return "PASS" if self.ok else "FAIL"

    @property
    def exit_code(self):
        return 0 if self.ok else 1


def _absolute(path):
    value = os.fspath(path)
    if not os.path.isabs(value) or "\x00" in value or "\\" in value:
        raise ValueError("expected an absolute POSIX path")
    if any(part in (".", "..") for part in value.split("/")):
        raise ValueError("dot/traversal components are forbidden")
    if os.path.normpath(value) != value:
        raise ValueError("absolute path must be canonical, without duplicate separators")
    return Path(value)


def _relative(value):
    if not isinstance(value, str) or not value or "\\" in value or "\x00" in value:
        raise ValueError("invalid relative path")
    parts = value.split("/")
    if any(part in ("", ".", "..") for part in parts) or value.startswith("/"):
        raise ValueError("absolute, empty, dot, and traversal components are forbidden")
    return PurePosixPath(value)


def _read_regular(path):
    """Open every component with O_NOFOLLOW and return bounded regular-file bytes."""
    path = _absolute(path)
    parts = path.parts
    directory = os.open("/", os.O_RDONLY | os.O_DIRECTORY)
    try:
        for part in parts[1:-1]:
            next_directory = os.open(
                part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                dir_fd=directory,
            )
            os.close(directory)
            directory = next_directory
        fd = os.open(
            parts[-1], os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | getattr(os, "O_NOATIME", 0),
            dir_fd=directory,
        )
        try:
            information = os.fstat(fd)
            if not stat.S_ISREG(information.st_mode):
                raise ValueError(f"not a regular file: {path}")
            if information.st_size > MAX_EVIDENCE_BYTES:
                raise ValueError(f"evidence/file exceeds size ceiling: {path}")
            chunks = []
            count = 0
            while True:
                chunk = os.read(fd, 1024 * 1024)
                if not chunk:
                    break
                count += len(chunk)
                if count > MAX_EVIDENCE_BYTES:
                    raise ValueError(f"file grew beyond size ceiling: {path}")
                chunks.append(chunk)
            payload = b"".join(chunks)
            if len(payload) != information.st_size:
                raise ValueError(f"file changed size while reading: {path}")
            return payload
        finally:
            os.close(fd)
    finally:
        os.close(directory)


def _read_json(path):
    payload = _read_regular(path)
    value = json.loads(payload.decode("utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected a JSON object: {path}")
    return value


def _expect(mapping, key, value):
    if key not in mapping:
        raise ValueError(f"missing required field: {key}")
    actual = mapping[key]
    if isinstance(value, bool):
        if type(actual) is not bool or actual is not value:
            raise ValueError(f"{key} must be boolean {value}")
    elif actual != value:
        raise ValueError(f"{key} must equal {value!r}")


def _safe_source_relative(value):
    relative = _relative(value)
    if relative.parts[0] not in {"docs", "artifacts"}:
        raise ValueError("copy source must be approved docs/artifacts evidence")
    if any(part.lower() in {"src", "results", "analysis", "scripts"}
           for part in relative.parts):
        raise ValueError("forbidden source directory")
    if "build" in (part.lower() for part in relative.parts):
        if str(relative) not in BUILD_SUMMARY_SOURCES:
            raise ValueError("only two explicitly reviewed build summaries are allowed")
    if relative.name in MARKET_NAMES:
        raise ValueError("market data may never be read as copied evidence")
    if relative.suffix.lower() == ".csv":
        if (relative.name != "csv_timestamp_summary.csv"
                or "phase1_timestamp_review" not in relative.parts
                or RUN_IDS["timestamp_review_run_id"] not in relative.parts):
            raise ValueError("only the named Timestamp Review summary CSV is allowed")
    elif relative.suffix.lower() not in {".json", ".md", ".txt", ".log", ".sha256"}:
        raise ValueError("unsupported evidence file type")
    return relative


def _market_object(value):
    if not isinstance(value, dict):
        return False
    keys = set(value)
    return (
        {"lastUpdateId", "bids", "asks"} <= keys
        or {"firstUpdateId", "finalUpdateId", "bids", "asks"} <= keys
        or {"U", "u", "b", "a"} <= keys
        or {"eventTime", "firstUpdateId", "finalUpdateId"} <= keys
    )


def _raw_market_content(payload):
    """Recognize raw top-level formats, not snippets embedded in reports/audits."""
    text = payload.decode("utf-8", errors="replace")
    stripped = text.lstrip("\ufeff \t\r\n")
    first = stripped.splitlines()[0] if stripped else ""
    columns = {part.strip().strip('"') for part in first.split(",")}
    if {"local_timestamp_us", "event_time_ms", "best_bid", "best_ask"} <= columns:
        return True
    if {"event_time_ms", "update_id", "bids", "asks"} <= columns:
        return True
    if stripped.startswith("{"):
        try:
            parsed = json.loads(stripped)
        except (json.JSONDecodeError, RecursionError):
            parsed = None
        if _market_object(parsed):
            return True
        # A normalized JSONL event file starts with an event object per line.
        for line in stripped.splitlines()[:3]:
            try:
                value = json.loads(line)
            except (json.JSONDecodeError, RecursionError):
                break
            if _market_object(value):
                return True
    return False


def _scan_project(root, result, permitted_summary_paths):
    """Inspect the new project only; no symlink following, writes or market reads."""
    try:
        root_mode = root.lstat().st_mode
        if not stat.S_ISDIR(root_mode):
            raise ValueError("project root must be a real directory")
        # Validate the root's ancestors even if it contains no files.
        for ancestor in root.parents:
            if not stat.S_ISDIR(ancestor.lstat().st_mode):
                raise ValueError(f"unsafe ancestor: {ancestor}")
    except (OSError, ValueError) as error:
        result.add("FAIL", "project_root", error)
        return
    inspected = 0
    pending = [root]
    while pending:
        directory = pending.pop()
        try:
            entries = sorted(os.scandir(directory), key=lambda entry: entry.name)
        except OSError as error:
            result.add("FAIL", "project_scan", error)
            continue
        for entry in entries:
            path = Path(entry.path)
            relative = path.relative_to(root).as_posix()
            try:
                mode = entry.stat(follow_symlinks=False).st_mode
                name = entry.name.lower()
                if stat.S_ISLNK(mode):
                    raise ValueError("symbolic link is forbidden")
                if name in {"src", "results", "build", "cmakefiles", ".ssh"}:
                    raise ValueError("forbidden copied/source/build directory or path")
                if stat.S_ISDIR(mode):
                    pending.append(path)
                    continue
                if not stat.S_ISREG(mode):
                    raise ValueError("non-regular project entry is forbidden")
                if (name == ".env" or name.startswith(".env.")
                        or name in {"id_rsa", "id_ed25519", "id_ecdsa", "id_dsa"}
                        or name.endswith((".pem", ".key", ".p12", ".pfx", ".crt",
                                          ".cer", ".der", ".tar.gz", ".tgz", ".7z",
                                          ".pkl", ".pickle", ".joblib", ".npy",
                                          ".npz", ".pt", ".pth", ".onnx", ".h5",
                                          ".hdf5", ".keras", ".safetensors"))):
                    raise ValueError("secret/certificate/archive/model file is forbidden")
                if entry.name in MARKET_NAMES:
                    raise ValueError("registered raw market filename is forbidden")
                if name.endswith(".csv") and relative not in permitted_summary_paths:
                    raise ValueError("only a hash-verified summary CSV copy is allowed")
                if name.endswith(".jsonl"):
                    raise ValueError("JSONL data files are not part of this handoff")
                payload = _read_regular(path)
                if payload.startswith(bytes((127, 69, 76, 70))):
                    raise ValueError("ELF executable magic detected")
                if PRIVATE_BLOCK.search(payload):
                    raise ValueError("private-key/certificate block detected")
                text = payload.decode("utf-8", errors="replace")
                credential_matches = list(CREDENTIAL_BINDING.finditer(text))
                credential_matches.extend(UNQUOTED_CREDENTIAL_BINDING.finditer(text))
                for match in credential_matches:
                    value = match.group(1).strip()
                    # Placeholder declarations and explanatory prose are not keys.
                    if (len(value) >= 8 and not any(c.isspace() for c in value)
                            and not PLACEHOLDER.fullmatch(value)):
                        raise ValueError("literal credential-like assignment detected")
                if _raw_market_content(payload):
                    raise ValueError("raw market record format detected")
                inspected += 1
            except (OSError, ValueError) as error:
                result.add("FAIL", "project_safety", f"{relative}: {error}")
    result.add("PASS", "project_scan_completed", f"{inspected} regular files inspected")


def verify_handoff(manifest_path, *, project_root=None,
                   expected_source_project=SOURCE_PROJECT,
                   expected_destination_project=DESTINATION_PROJECT):
    """Return checks; this function does not modify any inspected file."""
    result = VerificationResult()
    try:
        root = _absolute(project_root or DESTINATION_PROJECT)
        source_root = _absolute(expected_source_project)
        expected_root = _absolute(expected_destination_project)
        if root != expected_root:
            raise ValueError("project root differs from expected destination")
        manifest_path = Path(manifest_path)
        if not manifest_path.is_absolute():
            manifest_path = root / manifest_path
        manifest_path = _absolute(manifest_path)
        manifest_path.relative_to(root)
        manifest = _read_json(manifest_path)
        missing = sorted(set(MANIFEST_FIELDS) - set(manifest))
        if missing:
            raise ValueError(f"missing manifest fields: {missing}")
        _expect(manifest, "schema_version", "1.0")
        _expect(manifest, "source_project", str(source_root))
        _expect(manifest, "destination_project", str(expected_root))
        _expect(manifest, "phase1_v2_status", "PASS")
        _expect(manifest, "timestamp_review_status", "WARNING")
        _expect(manifest, "phase2_decision", "PASS_WITH_RESTRICTIONS")
        for key, value in RUN_IDS.items():
            _expect(manifest, key, value)
        for key in ("hft_source_modified", "network_activity_performed",
                    "trading_activity_performed", "model_training_performed"):
            _expect(manifest, key, False)
        _expect(manifest, "all_hashes_match", True)
        run_id = manifest["handoff_run_id"]
        if not isinstance(run_id, str) or not RUN_ID_RE.fullmatch(run_id):
            raise ValueError("invalid handoff UTC run_id")
        datetime.strptime(run_id, "%Y%m%dT%H%M%SZ")
        created = datetime.fromisoformat(manifest["created_at_utc"].replace("Z", "+00:00"))
        if created.utcoffset() is None or created.utcoffset().total_seconds() != 0:
            raise ValueError("created_at_utc must have UTC timezone")
        handoff_prefix = f"reference/hft_phase1/{run_id}/"
        expected_manifest = root / handoff_prefix / "HANDOFF_MANIFEST.json"
        if manifest_path != expected_manifest:
            raise ValueError("manifest path does not match its handoff run_id")
        copies = manifest["copied_files"]
        if not isinstance(copies, list) or not copies:
            raise ValueError("copied_files must be a nonempty list")
        for key in ("missing_files", "excluded_paths", "read_only_input_paths"):
            if not isinstance(manifest[key], list):
                raise ValueError(f"{key} must be a list")
        if not manifest["excluded_paths"]:
            raise ValueError("excluded_paths must document excluded inputs")
        if type(manifest["copied_file_count"]) is not int:
            raise ValueError("copied_file_count must be an integer")
        _expect(manifest, "copied_file_count", len(copies))
        result.add("PASS", "manifest", "required metadata and fixed safety declarations")
    except (OSError, ValueError, TypeError, KeyError) as error:
        result.add("FAIL", "manifest", error)
        return result

    permitted_summary_paths = set()
    destinations = set()
    sources = set()
    total_size = 0
    for index, item in enumerate(copies):
        try:
            if not isinstance(item, dict):
                raise ValueError("copy record must be an object")
            missing = sorted(set(COPY_FIELDS) - set(item))
            if missing:
                raise ValueError(f"missing copy fields: {missing}")
            relative_source = _safe_source_relative(item["source_relative_path"])
            relative_destination = _relative(item["destination_relative_path"])
            destination_text = str(relative_destination)
            if not destination_text.startswith(handoff_prefix):
                raise ValueError("copy destination is outside this handoff run")
            category = relative_destination.parts[3]
            if category not in {"reports", "manifests", "audits",
                                "timestamp_review", "environment"}:
                raise ValueError("copy destination category is not approved")
            if any(part.lower() in {"src", "results", "analysis", "scripts", "build"}
                   for part in relative_destination.parts):
                raise ValueError("forbidden copy destination path")
            source_path = _absolute(item["source_absolute_path"])
            if source_path != source_root / relative_source:
                raise ValueError("source absolute/relative paths disagree")
            if destination_text in destinations or str(relative_source) in sources:
                raise ValueError("duplicate source or destination in copy manifest")
            destinations.add(destination_text)
            sources.add(str(relative_source))
            _expect(item, "copy_status", "PASS")
            for key in ("source_sha256", "destination_sha256"):
                if not isinstance(item[key], str) or not HEX256.fullmatch(item[key]):
                    raise ValueError(f"{key} is not SHA-256")
            for key in ("source_size_bytes", "destination_size_bytes"):
                if type(item[key]) is not int or item[key] < 0:
                    raise ValueError(f"{key} is not a nonnegative integer")
            source_bytes = _read_regular(source_path)
            destination_bytes = _read_regular(root / relative_destination)
            source_hash = hashlib.sha256(source_bytes).hexdigest()
            destination_hash = hashlib.sha256(destination_bytes).hexdigest()
            if source_hash != destination_hash:
                raise ValueError("source and destination SHA-256 differ")
            if source_hash != item["source_sha256"]:
                raise ValueError("source SHA-256 differs from recorded digest")
            if destination_hash != item["destination_sha256"]:
                raise ValueError("destination SHA-256 differs from recorded digest")
            if len(source_bytes) != item["source_size_bytes"]:
                raise ValueError("source size differs from recorded size")
            if len(destination_bytes) != item["destination_size_bytes"]:
                raise ValueError("destination size differs from recorded size")
            total_size += len(destination_bytes)
            if relative_source.name == "csv_timestamp_summary.csv":
                permitted_summary_paths.add(destination_text)
            result.add("PASS", "copy", destination_text)
        except (OSError, ValueError, TypeError, KeyError, IndexError) as error:
            result.add("FAIL", "copy", f"record {index}: {error}")
    if (type(manifest["copied_total_size_bytes"]) is not int
            or manifest["copied_total_size_bytes"] != total_size):
        result.add("FAIL", "copied_total_size_bytes", "total differs from verified copies")
    else:
        result.add("PASS", "copied_total_size_bytes", total_size)

    try:
        data = _read_json(root / "configs/data_sources.json")
        _expect(data, "schema_version", "1.0")
        _expect(data, "access_mode", "read_only")
        _expect(data, "hft_project", str(source_root))
        _expect(data, "hft_results", str(source_root / "results"))
        _expect(data, "handoff_directory", handoff_prefix.rstrip("/"))
        for key in ("phase1_v2_run_id", "timestamp_review_run_id"):
            _expect(data, key, RUN_IDS[key])
        for key in ("allow_hft_write", "allow_network", "allow_real_trading",
                    "allow_testnet_trading", "allow_cross_session_labels"):
            _expect(data, key, False)
        _expect(data, "time_order_field", "event_time_ms")
        _expect(data, "local_timestamp_policy", "not_receive_time_do_not_use_for_latency")
        records = data.get("sources")
        if not isinstance(records, list) or len(records) != len(MARKET_NAMES):
            raise ValueError("sources must register all nine inputs")
        registered = set()
        input_paths = set()
        for record in records:
            if not isinstance(record, dict):
                raise ValueError("source metadata must be an object")
            missing = set(SOURCE_FIELDS) - set(record)
            if missing:
                raise ValueError(f"missing source metadata: {sorted(missing)}")
            relative = _relative(record["relative_path"])
            if relative.parts[0] != "results" or relative.name not in MARKET_NAMES:
                raise ValueError("unexpected source metadata path")
            absolute = _absolute(record["absolute_path"])
            if absolute != source_root / relative:
                raise ValueError("source metadata absolute/relative paths disagree")
            if relative.name in registered:
                raise ValueError("duplicate data source")
            registered.add(relative.name)
            input_paths.add(str(absolute))
            if not isinstance(record["sha256"], str) or not HEX256.fullmatch(record["sha256"]):
                raise ValueError("source metadata SHA-256 is missing/invalid")
            if type(record["size_bytes"]) is not int or record["size_bytes"] <= 0:
                raise ValueError("source metadata size is missing/invalid")
            if not isinstance(record["file_type"], str) or not record["file_type"]:
                raise ValueError("file_type is missing/invalid")
            if record["audit_status"] not in {"PASS", "WARNING"}:
                raise ValueError("source audit does not establish usable evidence")
            for key in ("allowed_uses", "prohibited_uses", "known_limitations"):
                if not isinstance(record[key], list) or not record[key]:
                    raise ValueError(f"{key} must be a nonempty list")
        if registered != MARKET_NAMES:
            raise ValueError("registered names differ from the required nine inputs")
        declared_inputs = manifest["read_only_input_paths"]
        if any(not isinstance(path, str) for path in declared_inputs):
            raise ValueError("read_only_input_paths must contain absolute path strings")
        if len(declared_inputs) != len(input_paths) or set(declared_inputs) != input_paths:
            raise ValueError("manifest read-only input paths differ from data-source registry")
        result.add("PASS", "data_sources", "nine metadata records; raw inputs were not opened")
    except (OSError, ValueError, TypeError, KeyError) as error:
        result.add("FAIL", "data_sources", error)

    try:
        policy = _read_json(root / "configs/timestamp_policy.json")
        _expect(policy, "ordering_field", "event_time_ms")
        for key in POLICY_FALSE:
            _expect(policy, key, False)
        for key in POLICY_TRUE:
            _expect(policy, key, True)
        _expect(policy, "max_match_error_ms", None)
        _expect(policy, "selection_status", SELECTION_STATUS)
        horizons = policy.get("horizons_ms", policy.get("horizons"))
        if horizons != [100, 200, 500, 1000]:
            raise ValueError("horizons must be [100, 200, 500, 1000] ms")
        labels = policy.get("required_label_fields", policy.get("label_fields"))
        if not isinstance(labels, list) or not REQUIRED_LABEL_FIELDS <= set(labels):
            raise ValueError("required per-label horizon/matching fields are incomplete")
        # No invented threshold is accepted as a final decision in this handoff.
        for key in ("max_gap_ms", "large_gap_threshold_ms"):
            if key in policy and policy[key] is not None:
                raise ValueError(f"{key} must remain null pending the research protocol")
        result.add("PASS", "timestamp_policy", "event ordering and unresolved thresholds preserved")
    except (OSError, ValueError, TypeError, KeyError) as error:
        result.add("FAIL", "timestamp_policy", error)

    try:
        experiment = _read_json(root / "configs/experiment_defaults.json")
        for key in EXPERIMENT_FALSE:
            _expect(experiment, key, False)
        for key in EXPERIMENT_TRUE:
            _expect(experiment, key, True)
        _expect(experiment, "scaler_fit", "training_only")
        _expect(experiment, "current_execution_seed", None)
        _expect(experiment, "max_match_error_ms", None)
        result.add("PASS", "experiment_defaults", "execution and overwrite gates disabled")
    except (OSError, ValueError, TypeError, KeyError) as error:
        result.add("FAIL", "experiment_defaults", error)

    _scan_project(root, result, permitted_summary_paths)
    if manifest["missing_files"]:
        result.add("WARNING", "missing_evidence", json.dumps(manifest["missing_files"], ensure_ascii=False))
    result.add("WARNING", "inherited_timestamp_status",
               "Timestamp Review remains WARNING; Phase 2 is PASS_WITH_RESTRICTIONS, not executed")
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, help="handoff manifest path within quantum-hft")
    args = parser.parse_args(argv)
    result = verify_handoff(args.manifest)
    for item in result.checks:
        print(f'[{item["status"]}] {item["check"]}: {item["detail"]}')
    print(f"HANDOFF VERIFICATION {result.status}; "
          f"failures={len(result.failures)}; warnings={len(result.warnings)}")
    return result.exit_code


if __name__ == "__main__":
    raise SystemExit(main())

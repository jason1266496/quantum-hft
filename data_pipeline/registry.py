"""Metadata-only registry for the nine explicitly handed-off HFT sources."""

from dataclasses import asdict, dataclass
import errno
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat


PRODUCTION_ROOT = Path("/home/jason/hft-realtime-codex")
EXPECTED_SOURCES = {
    "results/obi_market_data_20260827_session1.csv": "csv",
    "results/obi_market_data_20260827_session2.csv": "csv",
    "results/obi_market_data_20260827_session3.csv": "csv",
    "results/obi_market_data_test_20260827.csv": "csv",
    "results/obi_market_data.csv": "csv",
    "results/replay_snapshot_1000.json": "snapshot",
    "results/replay_events_1000.jsonl": "replay",
    "results/replay_snapshot_50000.json": "snapshot",
    "results/replay_events_50000.jsonl": "replay",
}
MAX_CONFIG_BYTES = 2 * 1024 * 1024


class RegistryError(ValueError):
    """Invalid registry metadata, identity or path boundary."""


class SourceValidationError(ValueError):
    """Source bytes or file identity differ from their registered evidence."""


def _absolute_path(value, field):
    if not isinstance(value, str) or not value or "\x00" in value:
        raise RegistryError(f"{field}: expected an absolute path")
    path = Path(value)
    if not path.is_absolute() or ".." in value.split("/"):
        raise RegistryError(f"{field}: absolute path without traversal required")
    if str(path) != value:
        raise RegistryError(f"{field}: non-canonical lexical path rejected")
    return path


def check_no_symlinks(path, *, require_regular=False):
    """Use lstat only. Reject symlinks in every component, including parents."""
    path = Path(path)
    if not path.is_absolute():
        raise RegistryError("Metadata path must be absolute")
    current = Path(path.anchor)
    parts = path.parts[1:]
    for index, part in enumerate(parts):
        current /= part
        try:
            info = current.lstat()
        except OSError as exc:
            raise RegistryError(f"Metadata unavailable: {current}: {exc.strerror}") from exc
        if stat.S_ISLNK(info.st_mode):
            raise RegistryError(f"Symbolic link rejected: {current}")
        if index < len(parts) - 1 and not stat.S_ISDIR(info.st_mode):
            raise RegistryError(f"Parent is not a directory: {current}")
    if not parts:
        info = path.lstat()
    if require_regular and not stat.S_ISREG(info.st_mode):
        raise RegistryError(f"Source is not a regular file: {path}")
    return info


def _strings(value, field):
    if not isinstance(value, list) or any(not isinstance(x, str) or not x for x in value):
        raise RegistryError(f"{field}: expected a list of non-empty strings")
    return tuple(value)


def _pairs_unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise RegistryError(f"Duplicate registry JSON key: {key}")
        result[key] = value
    return result


def _config_readonly_opener(path, flags):
    """Open configuration without following symlinks or allowing special files."""
    if flags & os.O_ACCMODE != os.O_RDONLY or flags & (os.O_CREAT | os.O_TRUNC | os.O_APPEND):
        raise RegistryError("Configuration must be opened read-only")
    path = Path(path)
    directory_flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC
    parent_fd = os.open(path.anchor, directory_flags)
    file_fd = None
    try:
        for part in path.parts[1:-1]:
            next_fd = os.open(part, directory_flags, dir_fd=parent_fd)
            os.close(parent_fd)
            parent_fd = next_fd
        file_flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC
        try:
            file_fd = os.open(path.name, file_flags | getattr(os, "O_NOATIME", 0), dir_fd=parent_fd)
        except OSError as exc:
            if exc.errno != errno.EPERM or not hasattr(os, "O_NOATIME"):
                raise
            file_fd = os.open(path.name, file_flags, dir_fd=parent_fd)
        if not stat.S_ISREG(os.fstat(file_fd).st_mode):
            raise RegistryError("Configuration must be a regular file")
        result, file_fd = file_fd, None
        return result
    finally:
        os.close(parent_fd)
        if file_fd is not None:
            os.close(file_fd)


@dataclass(frozen=True)
class DataSource:
    source_id: str
    session_id: str
    relative_path: str
    absolute_path: str
    file_type: str
    expected_sha256: str
    expected_size_bytes: int
    audit_status: str
    event_time_start: int | None
    event_time_end: int | None
    allowed_uses: tuple[str, ...]
    prohibited_uses: tuple[str, ...]
    known_limitations: tuple[str, ...]
    access_mode: str = "read_only"

    def to_dict(self):
        result = asdict(self)
        for key in ("allowed_uses", "prohibited_uses", "known_limitations"):
            result[key] = list(result[key])
        return result


class DatasetRegistry:
    """Register metadata without opening any market source.

    Production roots are fixed by default. Tests must explicitly provide their
    artificial root and disable the production nine-source requirement.
    """

    def __init__(self, config_path, *, allowed_roots=None, require_nine_sources=True):
        self.config_path = str(_absolute_path(str(Path(config_path).absolute()), "config_path"))
        roots = (PRODUCTION_ROOT,) if allowed_roots is None else tuple(allowed_roots)
        if not roots:
            raise RegistryError("At least one explicit allowed root is required")
        self.allowed_roots = tuple(_absolute_path(str(x), "allowed_root") for x in roots)
        for root in self.allowed_roots:
            info = check_no_symlinks(root)
            if not stat.S_ISDIR(info.st_mode):
                raise RegistryError(f"Allowed root is not a directory: {root}")
        try:
            check_no_symlinks(self.config_path, require_regular=True)
            with open(self.config_path, "r", encoding="utf-8", opener=_config_readonly_opener) as handle:
                raw = handle.read(MAX_CONFIG_BYTES + 1)
            if len(raw) > MAX_CONFIG_BYTES:
                raise RegistryError("Registry configuration exceeds size limit")
            config = json.loads(raw, object_pairs_hook=_pairs_unique)
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise RegistryError(f"Cannot parse registry configuration: {self.config_path}") from exc
        if not isinstance(config, dict):
            raise RegistryError("Registry configuration must be an object")
        required = {"schema_version", "access_mode", "hft_project", "hft_results", "allow_hft_write",
                    "allow_network", "allow_real_trading", "allow_testnet_trading", "allow_cross_session_labels",
                    "time_order_field", "local_timestamp_policy", "sources"}
        missing = required - config.keys()
        if missing:
            raise RegistryError(f"Missing registry fields: {', '.join(sorted(missing))}")
        if config["schema_version"] != "1.0":
            raise RegistryError("Unsupported registry schema_version")
        if config["access_mode"] != "read_only" or config["allow_hft_write"] is not False:
            raise RegistryError("Registry must prohibit writes and use read_only access")
        for flag in ("allow_network", "allow_real_trading", "allow_testnet_trading", "allow_cross_session_labels"):
            if config[flag] is not False:
                raise RegistryError(f"Forbidden enabled capability: {flag}")
        if config["time_order_field"] != "event_time_ms":
            raise RegistryError("Offline ordering must use event_time_ms metadata")
        if config["local_timestamp_policy"] != "not_receive_time_do_not_use_for_latency":
            raise RegistryError("Local timestamp policy must prohibit receive-time and latency claims")
        self.hft_project = _absolute_path(config["hft_project"], "hft_project")
        self.hft_results = _absolute_path(config["hft_results"], "hft_results")
        if self.hft_project not in self.allowed_roots:
            raise RegistryError("hft_project is not an explicitly allowed root")
        if self.hft_results != self.hft_project / "results":
            raise RegistryError("hft_results must be the registered root/results directory")
        if allowed_roots is None and self.hft_project != PRODUCTION_ROOT:
            raise RegistryError("Production HFT root cannot be redirected by configuration")
        items = config["sources"]
        if not isinstance(items, list) or not items:
            raise RegistryError("sources must be a non-empty list")
        if require_nine_sources and len(items) != 9:
            raise RegistryError("Production registry requires exactly nine sources")
        self._by_id = {}
        seen_paths = set()
        csv_sessions = set()
        source_fields = {"relative_path", "absolute_path", "file_type", "sha256", "size_bytes", "audit_status", "event_time_start", "event_time_end", "session_id", "allowed_uses", "prohibited_uses", "known_limitations"}
        for index, item in enumerate(items):
            if not isinstance(item, dict):
                raise RegistryError(f"Source {index}: expected object")
            missing = source_fields - item.keys()
            if missing:
                raise RegistryError(f"Source {index}: missing fields {', '.join(sorted(missing))}")
            relative = item["relative_path"]
            if not isinstance(relative, str) or "\x00" in relative:
                raise RegistryError(f"Source {index}: invalid relative_path")
            rel = PurePosixPath(relative)
            if rel.is_absolute() or ".." in relative.split("/") or str(rel) != relative or len(rel.parts) < 2 or rel.parts[0] != "results":
                raise RegistryError(f"Source {index}: relative path outside results or traversal")
            absolute = _absolute_path(item["absolute_path"], "absolute_path")
            if absolute != self.hft_project / relative or not absolute.is_relative_to(self.hft_results):
                raise RegistryError(f"Source {index}: absolute and relative paths escape or disagree")
            check_no_symlinks(absolute, require_regular=True)
            if relative in seen_paths:
                raise RegistryError(f"Source {index}: duplicate source path")
            seen_paths.add(relative)
            source_id = item.get("source_id", rel.stem)
            if not isinstance(source_id, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", source_id):
                raise RegistryError(f"Source {index}: invalid source_id")
            if source_id in self._by_id:
                raise RegistryError(f"Duplicate source_id: {source_id}")
            session_id = item["session_id"]
            if not isinstance(session_id, str) or not session_id.strip():
                raise RegistryError(f"Source {index}: session_id required")
            kind = item["file_type"]
            if kind not in ("csv", "snapshot", "replay"):
                raise RegistryError(f"Source {index}: unsupported file_type")
            if require_nine_sources and EXPECTED_SOURCES.get(relative) != kind:
                raise RegistryError(f"Source {index}: not one of the nine handed-off sources")
            if kind == "csv":
                if session_id in csv_sessions:
                    raise RegistryError("Different CSV files must have isolated research session IDs")
                csv_sessions.add(session_id)
            sha = item["sha256"]
            if not isinstance(sha, str) or not re.fullmatch(r"[0-9a-f]{64}", sha):
                raise RegistryError(f"Source {index}: expected lowercase SHA-256")
            size = item["size_bytes"]
            if type(size) is not int or size < 0:
                raise RegistryError(f"Source {index}: size_bytes must be non-negative integer")
            audit = item["audit_status"]
            if audit not in ("PASS", "WARNING", "FAIL", "NOT_AVAILABLE"):
                raise RegistryError(f"Source {index}: invalid audit_status")
            start, end = item["event_time_start"], item["event_time_end"]
            if kind == "snapshot":
                if start is not None or end is not None:
                    raise RegistryError("Snapshot event time is unavailable and must remain null")
            elif type(start) is not int or type(end) is not int or start < 0 or end < start:
                raise RegistryError(f"Source {index}: invalid event-time range")
            if item.get("access_mode", "read_only") != "read_only":
                raise RegistryError(f"Source {index}: write access rejected")
            self._by_id[source_id] = DataSource(
                source_id, session_id, relative, str(absolute), kind, sha, size,
                audit, start, end,
                _strings(item["allowed_uses"], "allowed_uses"),
                _strings(item["prohibited_uses"], "prohibited_uses"),
                _strings(item["known_limitations"], "known_limitations"),
            )
        self.sources = tuple(self._by_id.values())

    def get(self, source_id):
        if not isinstance(source_id, str) or source_id not in self._by_id:
            raise RegistryError("Requested source is not registered")
        return self._by_id[source_id]

    def snapshot(self):
        return {
            "schema_version": "1.0", "access_mode": "read_only",
            "hft_project": str(self.hft_project), "source_count": len(self.sources),
            "market_data_opened_by_registry": False,
            "session_id_semantics": "research isolation alias; historical capture ID NOT_AVAILABLE",
            "sources": [source.to_dict() for source in self.sources],
        }

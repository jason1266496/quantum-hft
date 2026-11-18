"""Read-only source validation and bounded parsing primitives."""

from contextlib import contextmanager
from decimal import Decimal, InvalidOperation
import errno
import hashlib
import io
import os
from pathlib import Path
import re
import stat
import time

from data_pipeline.registry import RegistryError, SourceValidationError, check_no_symlinks


MAX_NUMERIC_CHARACTERS = 128
HASH_CHUNK_BYTES = 1024 * 1024
MAX_LINE_CHARACTERS = 4 * 1024 * 1024


class DataFormatError(ValueError):
    def __init__(self, file, record_index, message, physical_line=None):
        self.file = str(file)
        self.record_index = record_index
        self.physical_line = physical_line
        location = f"{self.file}: record {record_index}"
        if physical_line is not None:
            location += f", physical line {physical_line}"
        super().__init__(f"{location}: {message}")


def parse_integer(value, *, file, record_index, field, physical_line=None, minimum=None):
    """Parse a bounded base-10 integer, rejecting bool, float and exponent notation."""
    if type(value) is int and value.bit_length() <= 425:
        result = value
    elif isinstance(value, str) and len(value) <= MAX_NUMERIC_CHARACTERS and re.fullmatch(r"[+-]?[0-9]+", value):
        result = int(value)
    else:
        raise DataFormatError(file, record_index, f"{field}: expected a decimal integer", physical_line)
    if minimum is not None and result < minimum:
        raise DataFormatError(file, record_index, f"{field}: integer below minimum", physical_line)
    return result


def parse_decimal(value, *, file, record_index, field, physical_line=None, minimum=None):
    """Parse finite bounded exact decimals without binary floating-point coercion."""
    if not isinstance(value, (str, Decimal, int)) or isinstance(value, bool):
        raise DataFormatError(file, record_index, f"{field}: expected an exact decimal", physical_line)
    text = str(value)
    if (not text or len(text) > MAX_NUMERIC_CHARACTERS or
            not re.fullmatch(r"[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?", text)):
        raise DataFormatError(file, record_index, f"{field}: invalid decimal length or whitespace", physical_line)
    try:
        result = Decimal(text)
        if not result.is_finite() or abs(result.as_tuple().exponent) > 100:
            raise InvalidOperation
    except (InvalidOperation, ValueError):
        raise DataFormatError(file, record_index, f"{field}: invalid finite decimal", physical_line) from None
    if minimum is not None and result < minimum:
        raise DataFormatError(file, record_index, f"{field}: decimal below minimum", physical_line)
    return result


def _signature(info):
    return (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns, info.st_mode)


class BaseAdapter:
    """Base interface: only registered regular files can be opened read-only.

    SHA-256 necessarily reads every byte in bounded chunks. Schema inspection
    remains a separate bounded sample operation; it is not a full-record scan.
    """

    def __init__(self, registry, source_id):
        self.registry = registry
        self.source = registry.get(source_id)
        self.closed = False
        self._validated_signature = None
        self._validation = None
        self._last_summary = None
        self._handles = set()

    def _ensure_open(self):
        if self.closed:
            raise SourceValidationError(f"Adapter is closed: {self.source.source_id}")

    def _current_signature(self):
        self._ensure_open()
        try:
            return _signature(check_no_symlinks(self.source.absolute_path, require_regular=True))
        except (OSError, RegistryError) as exc:
            raise SourceValidationError(f"Unsafe or unavailable source: {self.source.absolute_path}") from exc

    @contextmanager
    def _secure_binary(self):
        """Resolve each component with openat/O_NOFOLLOW, never a writable mode."""
        self._ensure_open()
        path = Path(self.source.absolute_path)
        flags_dir = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC
        parent_fd = None
        file_fd = None
        handle = None
        try:
            parent_fd = os.open(path.anchor, flags_dir)
            for part in path.parts[1:-1]:
                next_fd = os.open(part, flags_dir, dir_fd=parent_fd)
                os.close(parent_fd)
                parent_fd = next_fd
            flags_file = os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC | os.O_NONBLOCK
            try:
                file_fd = os.open(path.name, flags_file | getattr(os, "O_NOATIME", 0), dir_fd=parent_fd)
            except OSError as exc:
                if exc.errno != errno.EPERM or not hasattr(os, "O_NOATIME"):
                    raise
                file_fd = os.open(path.name, flags_file, dir_fd=parent_fd)
            info = os.fstat(file_fd)
            if not stat.S_ISREG(info.st_mode):
                raise SourceValidationError(f"Source is not a regular file: {path}")
            handle = os.fdopen(file_fd, "rb")
            file_fd = None
            self._handles.add(handle)
        except OSError as exc:
            raise SourceValidationError(f"Cannot safely open source read-only: {path}: {exc.strerror}") from exc
        finally:
            if parent_fd is not None:
                os.close(parent_fd)
            if file_fd is not None:
                os.close(file_fd)
        try:
            yield handle
        finally:
            handle.close()
            self._handles.discard(handle)

    @contextmanager
    def _open_binary(self):
        self.validate_source()
        with self._secure_binary() as handle:
            before = _signature(os.fstat(handle.fileno()))
            if before != self._validated_signature:
                raise SourceValidationError(f"Source changed after validation: {self.source.absolute_path}")
            try:
                yield handle
            finally:
                if not self.closed:
                    after = _signature(os.fstat(handle.fileno()))
                    if after != before or self._current_signature() != before:
                        self._validation = None
                        self._validated_signature = None
                        raise SourceValidationError(f"Source changed while reading: {self.source.absolute_path}")

    @contextmanager
    def _open_text(self):
        with self._open_binary() as binary:
            text = io.TextIOWrapper(binary, encoding="utf-8", errors="strict", newline="")
            try:
                yield text
            finally:
                # Keep the underlying descriptor alive for the binary identity check.
                try:
                    text.detach()
                except ValueError:
                    if not self.closed:
                        raise

    def validate_source(self, progress=None):
        """Hash the bytes on every call; equal stat metadata is not proof of identity."""
        self._ensure_open()
        current = self._current_signature()
        self._validation = None
        self._validated_signature = None
        started = time.monotonic()
        processed = 0
        total = self.source.expected_size_bytes
        last_progress = started

        def notify():
            if progress is not None:
                elapsed = time.monotonic() - started
                progress({"source_id": self.source.source_id, "processed_bytes": processed,
                          "total_bytes": total, "percent": min(100.0, processed * 100.0 / total) if total else 100.0,
                          "elapsed_seconds": elapsed,
                          "eta_seconds": max(0.0, total - processed) * elapsed / processed if processed else None,
                          "parse_errors": 0, "operation": "sha256_bytes_only"})

        notify()
        digest = hashlib.sha256()
        with self._secure_binary() as handle:
            before = _signature(os.fstat(handle.fileno()))
            if before != current:
                raise SourceValidationError(f"Source changed before hashing: {self.source.absolute_path}")
            while True:
                chunk = handle.read(HASH_CHUNK_BYTES)
                if not chunk:
                    break
                digest.update(chunk)
                processed += len(chunk)
                if time.monotonic() - last_progress >= 0.25:
                    notify()
                    last_progress = time.monotonic()
            after = _signature(os.fstat(handle.fileno()))
        notify()
        if before != after or self._current_signature() != before:
            raise SourceValidationError(f"Source changed while hashing: {self.source.absolute_path}")
        actual_sha = digest.hexdigest()
        if processed != self.source.expected_size_bytes:
            raise SourceValidationError(f"Source size mismatch: {self.source.absolute_path}: expected {self.source.expected_size_bytes}, actual {processed}")
        if actual_sha != self.source.expected_sha256:
            raise SourceValidationError(f"Source SHA-256 mismatch: {self.source.absolute_path}")
        self._validated_signature = before
        self._validation = {
            "status": "PASS", "source_id": self.source.source_id,
            "expected_sha256": self.source.expected_sha256, "actual_sha256": actual_sha,
            "expected_size_bytes": self.source.expected_size_bytes, "actual_size_bytes": processed,
            "sha256_match": True, "size_match": True, "hash_scope": "all_bytes_streamed",
            "schema_full_scan": False,
        }
        return dict(self._validation)

    def inspect_schema(self, sample_records=100):
        raise NotImplementedError("A format-specific adapter must implement schema inspection")

    def stream_records(self, limit=None):
        raise NotImplementedError("A format-specific adapter must implement record streaming")

    def summarize(self):
        self._ensure_open()
        return dict(self._last_summary) if self._last_summary is not None else self.inspect_schema()

    def close(self):
        self.closed = True
        for handle in tuple(self._handles):
            handle.close()
        self._handles.clear()

    def __enter__(self):
        self._ensure_open()
        return self

    def __exit__(self, exc_type, exc, traceback):
        self.close()
        return False

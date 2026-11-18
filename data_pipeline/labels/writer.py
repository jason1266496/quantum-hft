"""Exclusive, deterministic UTF-8/LF label CSV and JSON outputs."""
import csv
import hashlib
import json
from pathlib import Path
from .schema import LABEL_FIELDS, DECIMAL_FIELDS, INTEGER_FIELDS, STRING_FIELDS, decimal_text
from .validator import validate_label

def sha256_file(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()

def write_json(path, value):
    target = Path(path)
    encoded = (json.dumps(value, ensure_ascii=False, sort_keys=True,
                          indent=2, allow_nan=False) + "\n").encode("utf-8")
    with target.open("xb") as handle:
        handle.write(encoded)
    return sha256_file(target)

class LabelWriter:
    def __init__(self, path):
        self.path = Path(path)
        self.handle = self.path.open("x", encoding="utf-8", newline="")
        self.writer = csv.writer(self.handle, lineterminator="\n")
        self.writer.writerow(LABEL_FIELDS)
        self.row_count = 0
        self.identity = None
        self.result = None

    def write(self, row):
        validate_label(row)
        identity = (row["source_id"], row["session_id"], row["feature_view"])
        if self.identity is None:
            self.identity = identity
        elif identity != self.identity:
            raise ValueError("CROSS_SOURCE_SESSION_OR_VIEW_OUTPUT")
        cells = []
        for key in LABEL_FIELDS:
            value = row[key]
            if value is None:
                cells.append("")
            elif key in DECIMAL_FIELDS:
                cells.append(decimal_text(value))
            elif key in INTEGER_FIELDS:
                if type(value) is not int:
                    raise ValueError("INTEGER_REQUIRED")
                cells.append(str(value))
            elif key == "valid_label":
                cells.append("true" if value else "false")
            elif key in STRING_FIELDS:
                if type(value) is not str:
                    raise ValueError("STRING_REQUIRED")
                cells.append(value)
            else:
                raise ValueError("UNKNOWN_FIELD")
        self.writer.writerow(cells)
        self.row_count += 1

    def close(self):
        if self.result is None:
            self.handle.close()
            self.result = {"row_count": self.row_count, "sha256": sha256_file(self.path),
                           "size_bytes": self.path.stat().st_size}
        return dict(self.result)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()
        return False

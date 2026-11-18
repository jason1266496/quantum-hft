"""Exclusive directory guards for the research handoff; Python standard library only."""
from pathlib import Path
import os
import re
import stat

_RUN_ID = re.compile(r"[0-9]{8}T[0-9]{6}Z\Z")

def _reject_symlink_ancestors(path):
    """Inspect existing ancestors without resolving through symbolic links."""
    path = Path(os.path.abspath(os.fspath(path)))
    for item in (path, *path.parents):
        try:
            mode = item.lstat().st_mode
        except FileNotFoundError:
            continue
        if stat.S_ISLNK(mode):
            raise ValueError(f"symbolic link is forbidden: {item}")
        if not stat.S_ISDIR(mode):
            raise ValueError(f"not a directory: {item}")
    return path

def initialize_empty_root(path):
    """Create an absent root, or accept an empty root; never clean or merge it."""
    path = _reject_symlink_ancestors(path)
    try:
        path.mkdir()
    except FileExistsError:
        if any(path.iterdir()):
            raise FileExistsError(f"refusing nonempty project root: {path}")
    return path

def create_unique_handoff_run(root, run_id):
    """Exclusively create reference/hft_phase1/<run_id>; an existing run fails."""
    if not isinstance(run_id, str) or not _RUN_ID.fullmatch(run_id):
        raise ValueError("run_id must have UTC format YYYYMMDDTHHMMSSZ")
    root = _reject_symlink_ancestors(root)
    if not root.is_dir():
        raise FileNotFoundError(root)
    parent = root
    for component in ("reference", "hft_phase1"):
        parent = parent / component
        _reject_symlink_ancestors(parent)
        try:
            parent.mkdir()
        except FileExistsError:
            _reject_symlink_ancestors(parent)
    run = parent / run_id
    # No exist_ok, cleanup, merge, or overwrite operation is permitted.
    run.mkdir()
    return run

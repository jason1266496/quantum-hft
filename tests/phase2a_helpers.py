"""Artificial Phase 2A fixtures; never use production HFT data."""

import hashlib
import json
from pathlib import Path


def make_registry_fixture(base_dir, payloads):
    """Write synthetic (filename, file_type, text) inputs under a tests temporary dir."""
    base = Path(base_dir).absolute()
    tests_root = Path(__file__).absolute().parent
    if not base.is_relative_to(tests_root):
        raise ValueError("Phase 2A artificial fixtures must remain under tests/")
    root = base / "fake_hft"
    results = root / "results"
    results.mkdir(parents=True, exist_ok=False)
    sources = []
    for filename, kind, payload in payloads:
        if Path(filename).name != filename:
            raise ValueError("Fixture filenames must be plain basenames")
        path = results / filename
        data = payload.encode("utf-8") if isinstance(payload, str) else payload
        with path.open("xb") as handle:
            handle.write(data)
        sources.append({
            "relative_path": f"results/{filename}", "absolute_path": str(path),
            "file_type": kind, "sha256": hashlib.sha256(data).hexdigest(),
            "size_bytes": len(data), "audit_status": "PASS",
            "event_time_start": None if kind == "snapshot" else 1000,
            "event_time_end": None if kind == "snapshot" else 5000,
            "session_id": f"synthetic_{Path(filename).stem}",
            "allowed_uses": ["synthetic_unit_test"],
            "prohibited_uses": ["source_write", "network_latency", "cross_session_labels"],
            "known_limitations": ["artificial data only"],
        })
    config = {
        "schema_version": "1.0", "access_mode": "read_only", "allow_hft_write": False,
        "allow_network": False, "allow_real_trading": False, "allow_testnet_trading": False,
        "allow_cross_session_labels": False, "time_order_field": "event_time_ms",
        "local_timestamp_policy": "not_receive_time_do_not_use_for_latency",
        "hft_project": str(root), "hft_results": str(results), "sources": sources,
    }
    config_path = base / "data_sources.json"
    with config_path.open("x", encoding="utf-8") as handle:
        json.dump(config, handle, indent=2)
    return config_path, root

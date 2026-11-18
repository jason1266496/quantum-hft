"""Phase 2B deterministic, offline, streaming reconstruction of registered pairs."""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime
import csv
import gzip
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
from data_pipeline.adapters.snapshot_adapter import SnapshotAdapter
from data_pipeline.adapters.replay_adapter import ReplayAdapter
from data_pipeline.orderbook.types import Snapshot, Event, BookError
from data_pipeline.orderbook.rebuilder import OrderBookRebuilder
from data_pipeline.orderbook.reference import ReferenceOrderBookRebuilder
from data_pipeline.orderbook.canonical import canonical_state, canonical_state_hash, canonical_decimal

PAIRS = {
    ("replay_snapshot_1000", "replay_events_1000"): ("replay_1000", 1000),
    ("replay_snapshot_50000", "replay_events_50000"): ("replay_50000", 50000),
}
SPECIAL_CHECKPOINTS = {1, 10, 100, 1000, 5000, 10000, 25000}
CONTINUITY_FIELDS = ["repeat", "record_index", "event_time", "U", "u",
                     "previous_local_update_id", "classification", "action"]
HASH_FIELDS = ["repeat", "record_index", "reason", "local_update_id",
               "bid_level_count", "ask_level_count", "primary_hash", "reference_hash", "match"]


def _path(value, root):
    raw = os.fspath(value)
    if "\\" in raw or "\x00" in raw or ".." in raw.split("/"):
        raise ValueError("unsafe path")
    path = Path(raw) if os.path.isabs(raw) else root / raw
    for component in (path, *path.parents):
        if component.is_symlink():
            raise ValueError("symbolic links are forbidden")
    return path


def _json(path, value):
    with path.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2, allow_nan=False)
        handle.write("\n")


def _snapshot(adapter):
    """Exhaust the existing adapter; its metadata arrives only after validation."""
    levels = {"bids": [], "asks": []}
    metadata = None
    for row in adapter.stream_records():
        if row["source_id"] != adapter.source.source_id or row["session_id"] != adapter.source.session_id:
            raise ValueError("Snapshot adapter identity mismatch")
        if row["record_type"] == "snapshot_level":
            if metadata is not None:
                raise ValueError("Snapshot level after metadata")
            levels[row["side"]].append((row["price"], row["quantity"]))
        elif row["record_type"] == "snapshot_metadata":
            if metadata is not None:
                raise ValueError("duplicate Snapshot metadata")
            metadata = row
        else:
            raise ValueError("unsupported Snapshot record")
    if metadata is None:
        raise ValueError("Snapshot metadata not available")
    return Snapshot(adapter.source.source_id, adapter.source.session_id,
                    metadata["lastUpdateId"], tuple(levels["bids"]), tuple(levels["asks"]))


def _light(book):
    bid, ask = book.best_bid(), book.best_ask()
    return {
        "local_update_id": book.local_update_id,
        "best_bid": canonical_decimal(bid) if bid is not None else None,
        "best_ask": canonical_decimal(ask) if ask is not None else None,
        "crossed": bid is not None and ask is not None and bid >= ask,
        "empty": bid is None or ask is None,
    }


def _top(book):
    return {side: [[canonical_decimal(p), canonical_decimal(q)] for p, q in fn(5)]
            for side, fn in (("bids", book.top_bids), ("asks", book.top_asks))}


def _difference(left, right):
    """All differing levels are retained, without truncating mismatch evidence."""
    result = {"local_update_id": [left["local_update_id"], right["local_update_id"]]}
    for side in ("bids", "asks"):
        a, b = left[side], right[side]
        result[side] = [
            {"price": canonical_decimal(price),
             "primary": canonical_decimal(a[price]) if price in a else None,
             "reference": canonical_decimal(b[price]) if price in b else None}
            for price in sorted(a.keys() | b.keys(), reverse=side == "bids")
            if a.get(price) != b.get(price)
        ]
    return result


def _numeric_error_field(error):
    """Classify an explicit numeric diagnostic, never words in a raw summary."""
    message = str(error).split("; source_id=", 1)[0]
    match = re.search(r": (price|quantity) must be (?:a JSON number|a finite nonnegative decimal within numeric bounds|positive)$", message)
    if match:
        return match.group(1)
    match = re.search(r"(?:bids|asks)\[[0-9]+\]\.(price|quantity)(?:: (?:decimal below minimum|invalid finite decimal|invalid decimal length or whitespace|expected an exact decimal)| must be positive)$", message)
    return match.group(1) if match else None


def rebuild_pair(config_path, snapshot_source_id, replay_source_id, output_path, *,
                 compare_reference=False, repeat=2, progress_every=1000,
                 project_root=PROJECT_ROOT, allowed_roots=None,
                 require_nine_sources=True, progress_stream=None, command=None):
    """Alternate roots are explicit artificial-test injection; CLI cannot set them."""
    if type(repeat) is not int or repeat < 1:
        raise ValueError("repeat must be a positive integer")
    if type(progress_every) is not int or progress_every < 1:
        raise ValueError("progress_every must be a positive integer")
    if type(compare_reference) is not bool:
        raise ValueError("compare_reference must be boolean")
    root = _path(project_root, Path.cwd()).absolute()
    config = _path(config_path, root)
    output = _path(output_path, root)
    if not config.is_relative_to(root):
        raise ValueError("config must be within the research project")
    pair = PAIRS.get((snapshot_source_id, replay_source_id))
    if pair is None:
        raise ValueError("only the two explicitly approved Snapshot/Replay pairs are allowed")
    pair_name, estimated_total = pair
    if (output.parent.parent != root / "artifacts/phase2b" or output.name != pair_name
            or not re.fullmatch(r"[0-9]{8}T[0-9]{6}Z", output.parent.name)):
        raise ValueError("output must be artifacts/phase2b/<UTC_RUN_ID>/<approved_pair>")
    datetime.strptime(output.parent.name, "%Y%m%dT%H%M%SZ")
    if os.path.lexists(output):
        raise FileExistsError("output exists; refusing overwrite")
    registry = DatasetRegistry(config, allowed_roots=allowed_roots,
                               require_nine_sources=require_nine_sources)
    snapshot_source, replay_source = registry.get(snapshot_source_id), registry.get(replay_source_id)
    if snapshot_source.file_type != "snapshot" or replay_source.file_type != "replay":
        raise ValueError("incorrect source types")
    if snapshot_source.session_id != replay_source.session_id:
        raise ValueError("cross-session pairing forbidden")
    if any(output.is_relative_to(p) for p in registry.allowed_roots):
        raise ValueError("HFT output forbidden")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.mkdir(exist_ok=False)
    started = time.monotonic()
    progress_stream = sys.stdout if progress_stream is None else progress_stream
    source_validation = {"status": "NOT_AVAILABLE", "sources": [],
                         "validation_stage": "initial_full_sha256_and_size_then_adapter_identity_checks",
                         "subsequent_validation_failures": []}
    attempts, failures, comparisons = [], [], []
    mismatch_count = 0
    all_full_checks = all_light_checks = 0
    final_state = None
    first_summary = None
    def emit(payload, handle):
        text = json.dumps(payload, ensure_ascii=False, allow_nan=False)
        print(text, file=handle, flush=True)
        print(text, file=progress_stream, flush=True)

    with (output / "stdout.txt").open("x", encoding="utf-8") as stdout, \
         (output / "stderr.txt").open("x", encoding="utf-8") as stderr, \
         (output / "continuity_events.csv").open("x", newline="") as continuity_file, \
         (output / "checkpoint_state_hashes.csv").open("x", newline="") as hash_file, \
         (output / "top_levels_checkpoints.jsonl").open("x", encoding="utf-8") as top_file:
        writer = csv.DictWriter(continuity_file, fieldnames=CONTINUITY_FIELDS)
        writer.writeheader()
        hashes = csv.DictWriter(hash_file, fieldnames=HASH_FIELDS)
        hashes.writeheader()
        try:
            for adapter_type, source_id in ((SnapshotAdapter, snapshot_source_id), (ReplayAdapter, replay_source_id)):
                with adapter_type(registry, source_id) as adapter:
                    source_validation["sources"].append(adapter.validate_source())
            source_validation["status"] = "PASS"
            for attempt in range(1, repeat + 1):
                main = OrderBookRebuilder(replay_source.session_id, snapshot_source_id, replay_source_id)
                reference = (ReferenceOrderBookRebuilder(replay_source.session_id, snapshot_source_id, replay_source_id)
                             if compare_reference else None)
                tally = Counter()
                records = 0
                parsed = 0
                parse_errors = invalid_price = invalid_quantity = 0
                complete = False
                bridge = None
                snapshot = None
                first_valid = None
                attempt_error = None
                full_checks = light_checks = 0
                last_checkpoint = None
                t0 = time.monotonic()

                def progress(done=False):
                    total = parsed if done else estimated_total
                    elapsed = time.monotonic() - t0
                    emit({"stage": "rebuild", "repeat": attempt, "event_count": parsed,
                          "total_events": total, "total_is_estimate": not done,
                          "percent": 100.0 if done else min(100.0, parsed * 100.0 / total),
                          "elapsed_seconds": round(elapsed, 6),
                          "eta_seconds": round(max(0, total-parsed)*elapsed/parsed, 6) if parsed else "NOT_AVAILABLE",
                          "applied": main.applied_event_count, "skipped": main.skipped_event_count,
                          "gap": tally["UPDATE_ID_GAP"], "parse_error": parse_errors,
                          "complete": done}, stdout)

                def checkpoint(index, reason):
                    nonlocal full_checks, mismatch_count, last_checkpoint
                    primary = main.full_state()
                    phash = canonical_state_hash(primary)
                    rhash, equal = None, None
                    other = None
                    if reference:
                        other = reference.full_state()
                        rhash = canonical_state_hash(other)
                        equal = (primary == other and _light(main) == _light(reference)
                                 and _top(main) == _top(reference) and phash == rhash)
                        full_checks += 1
                    canonical = canonical_state(primary)
                    hashes.writerow({"repeat": attempt, "record_index": index, "reason": reason,
                                     "local_update_id": main.local_update_id,
                                     "bid_level_count": canonical["bid_level_count"],
                                     "ask_level_count": canonical["ask_level_count"],
                                     "primary_hash": phash, "reference_hash": rhash, "match": equal})
                    top_file.write(json.dumps({"repeat": attempt, "record_index": index, "reason": reason,
                                               **_light(main), "top5": _top(main)}) + "\n")
                    last_checkpoint = index
                    if equal is False:
                        mismatch_count += 1
                        _json(output / ("reference_mismatch_" + str(attempt) + "_" + str(index) + ".json"),
                              {"code": "REFERENCE_MISMATCH", "repeat": attempt, "record_index": index,
                               "difference": _difference(primary, other),
                               "primary_light": _light(main), "reference_light": _light(reference),
                               "primary_top5": _top(main), "reference_top5": _top(reference),
                               "primary_hash": phash, "reference_hash": rhash})
                        raise BookError("REFERENCE_MISMATCH", "complete state comparison failed")

                try:
                    with SnapshotAdapter(registry, snapshot_source_id) as adapter:
                        snapshot = _snapshot(adapter)
                    main.load_snapshot(snapshot)
                    if reference:
                        reference.load_snapshot(snapshot)
                    checkpoint(0, "INITIAL_SNAPSHOT")
                    progress()
                    with ReplayAdapter(registry, replay_source_id) as adapter:
                        stream = adapter.stream_records()
                        try:
                            for record in stream:
                                records = record["record_index"]
                                parsed += 1
                                event = Event.from_record(record)
                                decision = main.apply_event(event)
                                tally[decision["classification"]] += 1
                                writer.writerow({"repeat": attempt, **decision})
                                if first_valid is None and decision["classification"] != "STALE_BEFORE_SNAPSHOT":
                                    first_valid = {"record_index": records, "U": event.first_update_id,
                                                   "u": event.final_update_id}
                                    bridge = decision["action"] == "APPLY"
                                if reference:
                                    reference_decision = reference.apply_event(event)
                                    light_checks += 1
                                    if decision != reference_decision or _light(main) != _light(reference):
                                        mismatch_count += 1
                                        _json(output / ("reference_light_mismatch_" + str(attempt) + "_" + str(records) + ".json"),
                                              {"code": "REFERENCE_MISMATCH", "decision": decision,
                                               "reference_decision": reference_decision,
                                               "primary": _light(main), "reference": _light(reference),
                                               "difference": _difference(main.full_state(), reference.full_state())})
                                        raise BookError("REFERENCE_MISMATCH", "per-event comparison failed")
                                must_compare = ((pair_name == "replay_1000" and decision["action"] == "APPLY")
                                                or records in SPECIAL_CHECKPOINTS or records % 1000 == 0)
                                if must_compare:
                                    checkpoint(records, "APPLIED_EVENT" if pair_name == "replay_1000" else "CHECKPOINT")
                                if decision["action"] == "STOP":
                                    raise BookError(decision["classification"], "continuity stopped this pair")
                                if parsed % progress_every == 0:
                                    progress()
                            complete = True
                        finally:
                            stream.close()
                    # Always preserve an explicit final checkpoint, including an interval boundary.
                    checkpoint(records, "FINAL")
                except (ValueError, OSError, ArithmeticError) as exc:
                    attempt_error = {"type": type(exc).__name__, "code": getattr(exc, "code", "PARSE_OR_INPUT_ERROR"),
                                     "message": str(exc), "record_index": getattr(exc, "record_index", records)}
                    if isinstance(exc, DataFormatError):
                        parse_errors += 1
                        field = _numeric_error_field(exc)
                        invalid_price += int(field == "price")
                        invalid_quantity += int(field == "quantity")
                    elif isinstance(exc, SourceValidationError):
                        source_validation["status"] = "FAIL"
                        source_validation["subsequent_validation_failures"].append({"repeat": attempt, "message": str(exc)})
                    elif getattr(exc, "code", None) in ("INVALID_PRICE", "INVALID_QUANTITY"):
                        invalid_price += int(exc.code == "INVALID_PRICE")
                        invalid_quantity += int(exc.code == "INVALID_QUANTITY")
                    failures.append({"repeat": attempt, **attempt_error})
                    print(json.dumps(attempt_error), file=stderr, flush=True)
                finally:
                    if getattr(main, "local_update_id", None) is not None:
                        summary = main.state_summary()
                        state = main.full_state()
                        final_hash = canonical_state_hash(state)
                        if first_summary is None:
                            first_summary = summary
                            final_state = canonical_state(state)
                    else:
                        summary, final_hash = None, None
                    attempt_result = {
                        "repeat": attempt, "record_count": parsed, "last_record_index": records,
                        "fully_consumed": complete, "snapshot_last_update_id": snapshot.last_update_id if snapshot is not None else None,
                        "first_valid_event": first_valid, "bridge_pass": bridge,
                        "applied_events": main.applied_event_count, "skipped_events": main.skipped_event_count,
                        "stale_events": tally["STALE_BEFORE_SNAPSHOT"], "duplicate_events": tally["STALE_OR_DUPLICATE"],
                        "overlapping_events": tally["OVERLAPPING_CONTIGUOUS"],
                        "gaps": tally["UPDATE_ID_GAP"], "bridge_failures": tally["FIRST_EVENT_BRIDGE_FAILURE"],
                        "classification_counts": dict(sorted(tally.items())),
                        "parse_errors": parse_errors, "invalid_price": invalid_price, "invalid_quantity": invalid_quantity,
                        "crossed_book_count": main.crossed_book_count, "empty_side_count": main.empty_side_count,
                        "final_summary": summary, "final_state_hash": final_hash,
                        "reference_light_checks": light_checks, "reference_full_checks": full_checks,
                        "error": attempt_error, "elapsed_seconds": time.monotonic()-t0,
                    }
                    attempt_result["status"] = "PASS" if (
                        complete and bridge is True and not attempt_error and not parse_errors
                        and not invalid_price and not invalid_quantity and not main.continuity_error_count
                        and not main.crossed_book_count and not main.empty_side_count) else "FAIL"
                    attempts.append(attempt_result)
                    comparisons.append({"repeat": attempt, "light_checks": light_checks, "full_checks": full_checks})
                    all_full_checks += full_checks
                    all_light_checks += light_checks
                    progress(complete)
                if attempt_result["status"] != "PASS":
                    break
        except (ValueError, OSError, ArithmeticError) as exc:
            if source_validation["status"] != "PASS":
                source_validation["status"] = "FAIL"
            failures.append({"type": type(exc).__name__, "message": str(exc)})
            print(json.dumps(failures[-1]), file=stderr, flush=True)

    deterministic_keys = ("record_count", "snapshot_last_update_id", "first_valid_event", "bridge_pass",
                          "applied_events", "skipped_events", "classification_counts", "final_summary", "final_state_hash")
    repeat_equal = (len(attempts) == repeat and repeat >= 2 and all(
        all(item[key] == attempts[0][key] for key in deterministic_keys) for item in attempts[1:]))
    deterministic = {"status": "PASS" if repeat_equal else ("NOT_AVAILABLE" if repeat == 1 else "FAIL"),
                     "requested_repeats": repeat, "completed_repeats": len(attempts),
                     "compared_fields": list(deterministic_keys), "equal": repeat_equal,
                     "final_hashes": [x["final_state_hash"] for x in attempts]}
    reference_result = {
        "status": ("PASS" if not mismatch_count and all_full_checks and not failures else "FAIL")
                  if compare_reference else "NOT_AVAILABLE",
        "enabled": compare_reference, "mismatch_count": mismatch_count, "full_checks": all_full_checks,
        "per_event_checks": all_light_checks, "attempts": comparisons,
    }
    status = "PASS" if (source_validation["status"] == "PASS" and len(attempts) == repeat
                        and all(x["status"] == "PASS" for x in attempts)
                        and reference_result["status"] == "PASS" and deterministic["status"] == "PASS") else "FAIL"
    result = {"status": status, "pair": pair_name, "session_id": replay_source.session_id,
              "snapshot_source_id": snapshot_source_id, "replay_source_id": replay_source_id,
              "attempts": attempts, "reference_status": reference_result["status"],
              "deterministic_status": deterministic["status"], "failures": failures,
              "elapsed_seconds": time.monotonic()-started,
              "command": command, "hft_write": False, "network": False, "models": False,
              "features": False, "labels": False, "backtest": False, "paper_trading": False,
              "snapshot_scope": "known_snapshot_levels_plus_observed_updates",
              "raw_market_data_copied": False, "derived_book_state_saved": True}
    _json(output / "source_validation.json", source_validation)
    _json(output / "continuity_summary.json", {"status": status, "attempts": [
        {k: a[k] for k in ("repeat", "record_count", "snapshot_last_update_id", "first_valid_event", "bridge_pass",
                           "applied_events", "skipped_events", "stale_events", "duplicate_events",
                           "overlapping_events", "gaps", "bridge_failures", "classification_counts")}
        for a in attempts]})
    _json(output / "rebuild_summary.json", result)
    _json(output / "final_book_summary.json", first_summary)
    _json(output / "reference_comparison.json", reference_result)
    _json(output / "deterministic_repeat.json", deterministic)
    with (output / "final_book_state.json.gz").open("xb") as raw:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as compressed:
            compressed.write(json.dumps(final_state, sort_keys=True, separators=(",", ":"), allow_nan=False).encode())
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True)
    parser.add_argument("--snapshot-source-id", required=True)
    parser.add_argument("--replay-source-id", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--compare-reference", action="store_true")
    parser.add_argument("--repeat", type=int, default=2)
    parser.add_argument("--progress-every", type=int, default=1000)
    args = parser.parse_args(argv)
    try:
        result = rebuild_pair(args.config, args.snapshot_source_id, args.replay_source_id, args.output,
                              compare_reference=args.compare_reference, repeat=args.repeat,
                              progress_every=args.progress_every,
                              command=["python3", "tools/rebuild_orderbook.py", *(sys.argv[1:] if argv is None else argv)])
    except (ValueError, OSError) as exc:
        print(json.dumps({"status": "FAIL", "error": str(exc)}), file=sys.stderr)
        return 1
    print(json.dumps({"status": result["status"], "pair": result["pair"],
                      "record_counts": [a["record_count"] for a in result["attempts"]],
                      "final_hashes": [a["final_state_hash"] for a in result["attempts"]]}))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())


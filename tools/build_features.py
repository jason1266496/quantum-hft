"""Phase 2C streaming, session-isolated deterministic feature generation."""
from __future__ import annotations
import argparse
from collections import Counter
from contextlib import ExitStack
import csv
import json
import os
from pathlib import Path
import re
import sys
import time

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from data_pipeline.registry import DatasetRegistry, SourceValidationError
from data_pipeline.adapters.base import DataFormatError
from data_pipeline.adapters.csv_adapter import CSVAdapter
from data_pipeline.adapters.snapshot_adapter import SnapshotAdapter
from data_pipeline.adapters.replay_adapter import ReplayAdapter
from data_pipeline.orderbook.types import Snapshot, Event, BookError
from data_pipeline.orderbook.rebuilder import OrderBookRebuilder
from data_pipeline.orderbook.canonical import canonical_state, canonical_decimal
from data_pipeline.features.schema import VIEWS, fields, feature_schema, schema_hash
from data_pipeline.features.builder import FeatureBuilder
from data_pipeline.features.reference import reference_features
from data_pipeline.features.validator import FeatureValidator
from data_pipeline.features.writer import FeatureWriter, write_json

PAIRS = {"replay_events_1000": "replay_snapshot_1000",
         "replay_events_50000": "replay_snapshot_50000"}
CORE_REFERENCE_FIELDS = ("best_bid", "best_ask", "mid_price", "spread",
                         "bid_volume_5", "ask_volume_5", "obi_5")
ERROR_FIELDS = ("repeat", "source_id", "record_index", "feature_view",
                "code", "field", "main_value", "reference_value")
DIFFERENCE_FIELDS = ("repeat", "record_index", "field", "source_value",
                     "computed_value", "signed_difference", "absolute_difference", "within_tolerance")


def _path(value, root):
    raw = os.fspath(value)
    if "\\" in raw or "\x00" in raw or ".." in raw.split("/"):
        raise ValueError("unsafe path")
    path = Path(raw) if os.path.isabs(raw) else root / raw
    for component in (path, *path.parents):
        if component.is_symlink():
            raise ValueError("symlink forbidden")
    return path


def _estimate(config, source, root):
    """Use an existing audit count only when its byte fingerprint agrees."""
    raw = json.loads(config.read_text())
    for item in raw["sources"]:
        if item["relative_path"] != source.relative_path:
            continue
        name = item.get("metadata_evidence", {}).get("copied_audit_relative_path")
        if not name:
            return None
        path = _path(name, root)
        if not path.is_relative_to(root):
            raise ValueError("audit reference escapes project")
        evidence = json.loads(path.read_text())
        for entry in evidence["files"]:
            count = entry.get("records")
            if (entry.get("sha256") == source.expected_sha256
                    and entry.get("size_bytes") == source.expected_size_bytes
                    and type(count) is int and count >= 0):
                return count
    return None


def _snapshot(adapter):
    levels = {"bids": [], "asks": []}
    metadata = None
    for row in adapter.stream_records():
        if row["source_id"] != adapter.source.source_id or row["session_id"] != adapter.source.session_id:
            raise ValueError("snapshot identity mismatch")
        if row["record_type"] == "snapshot_level":
            levels[row["side"]].append((row["price"], row["quantity"]))
        else:
            if metadata is not None or row["record_type"] != "snapshot_metadata":
                raise ValueError("snapshot interface mismatch")
            metadata = row
    if metadata is None:
        raise ValueError("snapshot metadata unavailable")
    return Snapshot(adapter.source.source_id, adapter.source.session_id, metadata["lastUpdateId"],
                    tuple(levels["bids"]), tuple(levels["asks"]))


def _metadata(record, book):
    return {"source_id": record["source_id"], "session_id": record["session_id"],
            "record_index": record["record_index"], "event_time_ms": record["eventTime"],
            "first_update_id": record["firstUpdateId"], "final_update_id": record["finalUpdateId"],
            "local_update_id": book.local_update_id}


def _reference_state(book, full):
    if full:
        return canonical_state(book.full_state())
    # Exact canonical projection of current top five; no future event is read.
    state = canonical_state({"local_update_id": book.local_update_id,
                             "bids": dict(book.top_bids(5)), "asks": dict(book.top_asks(5))})
    state["state_scope"] = "TOP5_CANONICAL_PROJECTION"
    return state


def _csv_value(value):
    from decimal import Decimal
    if isinstance(value, Decimal):
        return canonical_decimal(value) if value.is_finite() else str(value)
    if value is None:
        return ""
    return str(value)


def build_source(config_path, source_id, feature_view, output_path, *,
                 compare_reference=False, repeat=1, progress_every=10000,
                 project_root=PROJECT_ROOT, allowed_roots=None,
                 require_nine_sources=True, progress_stream=None, command=None):
    if type(repeat) is not int or repeat < 1 or type(progress_every) is not int or progress_every < 1:
        raise ValueError("repeat and progress-every must be positive integers")
    if type(compare_reference) is not bool:
        raise ValueError("compare-reference must be boolean")
    root = _path(project_root, Path.cwd())
    if not root.resolve().is_relative_to(PROJECT_ROOT.resolve()):
        raise ValueError("project root must remain within Quantum-HFT")
    config = _path(config_path, root)
    output = _path(output_path, root)
    if not config.is_relative_to(root):
        raise ValueError("config must be within research project")
    if (output.parent.name != "sources" or output.parent.parent.parent != root/"artifacts/phase2c"
            or output.name != source_id
            or not re.fullmatch(r"[0-9]{8}T[0-9]{6}Z", output.parent.parent.name)):
        raise ValueError("output must be artifacts/phase2c/<UTC_RUN_ID>/sources/<source_id>")
    from datetime import datetime
    datetime.strptime(output.parent.parent.name, "%Y%m%dT%H%M%SZ")
    if os.path.lexists(output):
        raise FileExistsError("source output exists; refusing overwrite")
    registry = DatasetRegistry(config, allowed_roots=allowed_roots, require_nine_sources=require_nine_sources)
    source = registry.get(source_id)
    if source.file_type not in ("csv", "replay"):
        raise ValueError("features require one CSV or one paired Replay")
    if feature_view not in (*VIEWS, "both"):
        raise ValueError("unknown feature view")
    views = VIEWS if feature_view == "both" else (feature_view,)
    if source.file_type == "csv" and views != ("aggregate_core_v1",):
        raise ValueError("CSV cannot provide depth_top5_v1")
    snapshot_source = None
    if source.file_type == "replay":
        if source_id not in PAIRS:
            raise ValueError("unapproved replay pair")
        snapshot_source = registry.get(PAIRS[source_id])
        if snapshot_source.session_id != source.session_id or snapshot_source.file_type != "snapshot":
            raise ValueError("cross-session or incorrect snapshot pair")
    if any(output.is_relative_to(p) for p in registry.allowed_roots):
        raise ValueError("HFT output forbidden")
    estimate = _estimate(config, source, root)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.mkdir(exist_ok=False)
    source_manifest = {"source": source.to_dict(), "snapshot": snapshot_source.to_dict() if snapshot_source else None,
                       "status": "NOT_AVAILABLE", "validations": [], "historical_record_count": estimate,
                       "csv_local_timestamp_present_but_prohibited": source.file_type == "csv",
                       "csv_update_id_mapping": "direct_source_alias_only_not_rebuilt_book_or_range_proof",
                       "source_producer_identity": "UNKNOWN", "raw_market_data_copied": False}
    stream = progress_stream if progress_stream is not None else sys.stdout
    attempts, failures, comparison = [], [], {"enabled": compare_reference, "mismatch_count": 0,
                                             "light_checks": 0, "full_checks": 0, "checkpoints": [],
                                             "canonical_input_scopes": {}, "status": "NOT_AVAILABLE"}
    scopes = Counter()
    started = time.monotonic()
    with (output/"stdout.txt").open("x", encoding="utf-8") as stdout, \
         (output/"stderr.txt").open("x", encoding="utf-8") as stderr, \
         (output/"feature_errors.csv").open("x", encoding="utf-8", newline="") as errors_handle, \
         (output/"source_value_differences.csv").open("x", encoding="utf-8", newline="") as differences_handle:
        errors = csv.DictWriter(errors_handle, fieldnames=ERROR_FIELDS, lineterminator="\n")
        errors.writeheader()
        differences = csv.DictWriter(differences_handle, fieldnames=DIFFERENCE_FIELDS, lineterminator="\n")
        differences.writeheader()
        try:
            inputs = [(CSVAdapter if source.file_type=="csv" else ReplayAdapter, source_id)]
            if snapshot_source:
                inputs.insert(0, (SnapshotAdapter, snapshot_source.source_id))
            for cls, sid in inputs:
                with cls(registry, sid) as adapter:
                    source_manifest["validations"].append(adapter.validate_source())
            source_manifest["status"] = "PASS"
            for iteration in range(1, repeat+1):
                target = output if iteration == 1 else output/("repeat_"+str(iteration))
                if iteration > 1:
                    target.mkdir(exist_ok=False)
                builder = FeatureBuilder(source.source_id, source.session_id, source.file_type)
                validators = {v: FeatureValidator(source.source_id, source.session_id, v, source.file_type) for v in views}
                reference_validators = {v: FeatureValidator(source.source_id, source.session_id, v, source.file_type) for v in views}
                writers = {v: FeatureWriter(target/(v+".csv"), v, project_root=root) for v in views}
                input_count = output_count = parse_errors = 0
                continuity = Counter()
                book = None
                last_rows = last_reference_rows = last_reference_raw = last_metadata = None
                iteration_failed = False
                complete = False
                t0 = time.monotonic()
                def progress(done=False):
                    total = input_count if done else estimate
                    elapsed = time.monotonic()-t0
                    value = {"source_id": source_id, "repeat": iteration, "input_record_count": input_count,
                             "output_record_count": output_count, "total_records": total if total is not None else "NOT_AVAILABLE",
                             "total_basis": "actual_complete" if done else "prior_audit_count",
                             "percent": 100.0 if done else (min(100.0,input_count*100.0/total) if total else "NOT_AVAILABLE"),
                             "elapsed_seconds": round(elapsed,6),
                             "eta_seconds": round(max(0,total-input_count)*elapsed/input_count,6) if total is not None and input_count else "NOT_AVAILABLE",
                             "applied": book.applied_event_count if book else None,
                             "skipped": book.skipped_event_count if book else None,
                             "gap": continuity["UPDATE_ID_GAP"], "parse_error": parse_errors}
                    text=json.dumps(value,sort_keys=True)
                    print(text,file=stdout,flush=True);print(text,file=stream,flush=True)
                def compare(left,right,index,full):
                    keys = {v: fields(v) for v in views} if full else {"aggregate_core_v1":CORE_REFERENCE_FIELDS}
                    if not full and "aggregate_core_v1" not in views:
                        keys={v:fields(v) for v in views}
                    mismatches=[]
                    for view, columns in keys.items():
                        for field in columns:
                            if left[view].get(field) != right[view].get(field):
                                mismatch={"repeat":iteration,"source_id":source_id,"record_index":index,
                                          "feature_view":view,"code":"FEATURE_REFERENCE_MISMATCH","field":field,
                                          "main_value":_csv_value(left[view].get(field)),
                                          "reference_value":_csv_value(right[view].get(field))}
                                errors.writerow(mismatch);mismatches.append(mismatch)
                    comparison["mismatch_count"] += len(mismatches)
                    if full:
                        comparison["full_checks"]+=1
                        if source_id=="replay_events_50000":
                            comparison["checkpoints"].append({"repeat":iteration,"record_index":index})
                    else:
                        comparison["light_checks"]+=1
                    if mismatches:
                        raise ValueError("FEATURE_REFERENCE_MISMATCH")
                try:
                    if snapshot_source:
                        book=OrderBookRebuilder(source.session_id,snapshot_source.source_id,source_id)
                        with SnapshotAdapter(registry,snapshot_source.source_id) as adapter:
                            book.load_snapshot(_snapshot(adapter))
                    progress()
                    cls=CSVAdapter if source.file_type=="csv" else ReplayAdapter
                    with cls(registry,source_id) as adapter:
                        records=adapter.stream_records()
                        try:
                            for record in records:
                                input_count+=1
                                if book:
                                    event=Event.from_record(record)
                                    decision=book.apply_event(event)
                                    continuity[decision["classification"]]+=1
                                    if decision["action"]=="STOP":
                                        raise BookError(decision["classification"],"pair continuity failure")
                                    if decision["action"]=="SKIP":
                                        if input_count%progress_every==0:progress()
                                        continue
                                    raw=builder.from_book(book,event)
                                else:
                                    raw={"aggregate_core_v1":builder.from_csv(record)}
                                rows={v:validators[v].observe(raw[v],source_record=record if not book else None) for v in views}
                                for view,row in rows.items():
                                    if not row["valid_feature_row"]:
                                        errors.writerow({"repeat":iteration,"source_id":source_id,"record_index":record["record_index"],
                                                         "feature_view":view,"code":row["invalid_reason"]})
                                if book and compare_reference:
                                    full=(source_id=="replay_events_1000" or record["record_index"]%1000==0)
                                    state=_reference_state(book,full)
                                    scopes["FULL_CANONICAL_BOOK" if full else "TOP5_CANONICAL_PROJECTION"]+=1
                                    metadata=_metadata(record,book)
                                    reference_raw=reference_features(state,metadata)
                                    ref_rows={v:reference_validators[v].observe(reference_raw[v]) for v in views}
                                    compare(rows,ref_rows,record["record_index"],full)
                                    last_rows,last_reference_rows=rows,ref_rows
                                    last_reference_raw,last_metadata=reference_raw,metadata
                                for view in views:
                                    writers[view].write(rows[view])
                                if not book:
                                    # Preserve all three original/recomputed differences only in quality output.
                                    from decimal import Decimal, localcontext, Context, ROUND_HALF_EVEN
                                    with localcontext(Context(prec=50, rounding=ROUND_HALF_EVEN)):
                                        for field in ("mid_price","spread","obi_5"):
                                            original, calculated=record.get(field),rows["aggregate_core_v1"].get(field)
                                            delta=original-calculated if isinstance(original,Decimal) and isinstance(calculated,Decimal) else None
                                            differences.writerow({"repeat":iteration,"record_index":record["record_index"],"field":field,
                                                                  "source_value":_csv_value(original),"computed_value":_csv_value(calculated),
                                                                  "signed_difference":_csv_value(delta),"absolute_difference":_csv_value(abs(delta)) if delta is not None else "",
                                                                  "within_tolerance":str(abs(delta)<=Decimal("1e-8")).lower() if delta is not None else ""})
                                output_count+=1
                                if input_count%progress_every==0:progress()
                            complete=True
                        finally:
                            records.close()
                    if book and compare_reference and last_rows is not None:
                        # EOF is used only for verification. Previously written features are never revised.
                        last_full=reference_features(_reference_state(book,True),last_metadata)
                        for v in views:
                            if last_full[v]!=last_reference_raw[v]:
                                compare(last_reference_raw,last_full,last_metadata["record_index"],True)
                        if source_id=="replay_events_50000" and last_metadata["record_index"]%1000:
                            compare(last_rows,last_reference_rows,last_metadata["record_index"],True)
                    if not output_count:
                        raise ValueError("no feature rows emitted")
                except (ValueError,OSError,ArithmeticError) as exc:
                    iteration_failed=True
                    parse_errors+=int(isinstance(exc,DataFormatError))
                    if isinstance(exc,SourceValidationError):
                        source_manifest["status"]="FAIL"
                    failure={"repeat":iteration,"type":type(exc).__name__,"code":getattr(exc,"code",type(exc).__name__),
                             "message":str(exc),"record_index":getattr(exc,"record_index",input_count)}
                    failures.append(failure)
                    errors.writerow({"repeat":iteration,"source_id":source_id,"record_index":failure["record_index"],
                                     "code":failure["code"],"main_value":failure["message"]})
                    print(json.dumps(failure,sort_keys=True),file=stderr,flush=True)
                finally:
                    files={v:w.close() for v,w in writers.items()}
                    quality={v:q.summary() for v,q in validators.items()}
                    mismatch=any(q["source_value_mismatch_count"] for q in quality.values())
                    attempt={"repeat":iteration,"input_record_count":input_count,"output_record_count":output_count,
                             "fully_consumed":complete,"parse_errors":parse_errors,"views":files,"quality":quality,
                             "continuity":dict(sorted(continuity.items())),
                             "final_book_hash":book.canonical_state_hash() if book and book.local_update_id is not None else None,
                             "status":"PASS" if complete and output_count and not iteration_failed and not mismatch else "FAIL",
                             "elapsed_seconds":str(time.monotonic()-t0)}
                    attempts.append(attempt)
                    progress(complete)
                if attempt["status"]!="PASS":
                    break
        except (ValueError,OSError,ArithmeticError) as exc:
            source_manifest["status"]="FAIL"
            failures.append({"type":type(exc).__name__,"message":str(exc)})
            print(json.dumps(failures[-1],sort_keys=True),file=stderr,flush=True)
    comparison["canonical_input_scopes"]=dict(scopes)
    comparison["status"]=("PASS" if comparison["mismatch_count"]==0 and attempts
                          and comparison["light_checks"]+comparison["full_checks"]>0
                          and all(a["fully_consumed"] and a["status"]=="PASS" for a in attempts)
                          else "FAIL") if source.file_type=="replay" and compare_reference else "NOT_AVAILABLE"
    comparison["reason"]=None if source.file_type=="replay" else "CSV has no canonical per-level Book; source values are independently recalculated and audited"
    def deterministic_value(a):
        return {"input_record_count":a["input_record_count"],"output_record_count":a["output_record_count"],
                "views":{v:{k:f[k] for k in ("row_count","column_order","schema_hash","sha256")} for v,f in a["views"].items()},
                "quality":a["quality"],"continuity":a["continuity"],"final_book_hash":a["final_book_hash"]}
    equal=(repeat>=2 and len(attempts)==repeat and all(deterministic_value(a)==deterministic_value(attempts[0]) for a in attempts[1:]))
    determinism={"status":"PASS" if equal else ("NOT_AVAILABLE" if repeat==1 else "FAIL"),
                 "equal":equal,"requested_repeats":repeat,"completed_repeats":len(attempts),
                 "compared_fields":["row_count","column_order","schema_hash","output_sha256","quality_summary","final_book_hash"],
                 "runs":[deterministic_value(a) for a in attempts]}
    status="PASS" if (source_manifest["status"]=="PASS" and len(attempts)==repeat and all(a["status"]=="PASS" for a in attempts)
                      and (repeat==1 or equal) and (not compare_reference or source.file_type=="csv" or comparison["status"]=="PASS")) else "FAIL"
    if repeat>1 and not equal:
        failures.append({"code":"NON_DETERMINISTIC_OUTPUT"})
    feature_manifest={"status":status,"source_id":source_id,"session_id":source.session_id,"source_kind":source.file_type,
                      "views":list(views),"schema_hashes":{v:schema_hash(v) for v in views},"attempts":attempts,
                      "failures":failures,"elapsed_seconds":str(time.monotonic()-started),"command":command,
                      "numeric_policy":{"precision":50,"rounding":"ROUND_HALF_EVEN","float_used":False},
                      "hft_write":False,"network":False,"labels":False,"targets":False,"splits":False,"models":False,
                      "local_timestamp_in_features":False,"cross_session_merge":False,"snapshot_initial_rows":0}
    write_json(output/"source_manifest.json",source_manifest,project_root=root)
    write_json(output/"feature_manifest.json",feature_manifest,project_root=root)
    write_json(output/"feature_quality.json",{"status":status,"attempts":[a["quality"] for a in attempts],
                                             "invalid_rows_preserved":True,"parse_errors":[a["parse_errors"] for a in attempts]},project_root=root)
    write_json(output/"reference_comparison.json",comparison,project_root=root)
    write_json(output/"determinism.json",determinism,project_root=root)
    return feature_manifest


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config",required=True)
    parser.add_argument("--source-id",required=True)
    parser.add_argument("--feature-view",choices=(*VIEWS,"both"),required=True)
    parser.add_argument("--output",required=True)
    parser.add_argument("--compare-reference",action="store_true")
    parser.add_argument("--repeat",type=int,default=1)
    parser.add_argument("--progress-every",type=int,default=10000)
    args=parser.parse_args(argv)
    try:
        result=build_source(args.config,args.source_id,args.feature_view,args.output,
                            compare_reference=args.compare_reference,repeat=args.repeat,progress_every=args.progress_every,
                            command=["python3","tools/build_features.py",*(sys.argv[1:] if argv is None else argv)])
    except (ValueError,OSError) as exc:
        print(json.dumps({"status":"FAIL","error":str(exc)},sort_keys=True),file=sys.stderr)
        return 1
    print(json.dumps({"source_id":result["source_id"],"status":result["status"],
                      "rows":[a["output_record_count"] for a in result["attempts"]]},sort_keys=True))
    return 0 if result["status"]=="PASS" else 1


if __name__=="__main__":
    raise SystemExit(main())

